#!/usr/bin/env python3
"""Build a Cleeng user-import CSV from a source platform export.

The agent decides which source column feeds which Cleeng field (--map) and this
script does the rest the same way every time: normalisation, derivation of
locale/currency/timezone from the country, validation against the values the
Cleeng importer accepts, and the error report.

Usage:
  python3 scripts/build_import.py SOURCE.csv --out-dir OUT \
      --map email=email --map countryCode=address_country --map createDate=created_at \
      [--full-name-column name] [--external-sso] [--zip]

Writes OUT/cleeng_import.csv and, when any row has an issue, OUT/migration_errors.csv.
Prints a JSON summary on stdout. Exit codes: 0 done, 2 bad arguments or input.
Uses the Python standard library only.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import ipaddress
import json
import re
import sys
import zipfile
from pathlib import Path

# Column order the Cleeng user import checks with an exact, ordered header match.
TEMPLATE = [
    "email", "firstName", "lastName", "locale", "countryCode", "lastLogin",
    "createDate", "timezone", "currency", "externalId", "ipAddress", "passwordHash",
]
REFERENCE = Path(__file__).resolve().parent.parent / "assets" / "reference-data.json"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
BCRYPT_RE = re.compile(r"^\$2[abxy]\$\d{2}\$[./A-Za-z0-9]{53}$")
DEFAULT_LOCALE = "en_US"
DEFAULT_CURRENCY = "EUR"
NAME_MAX = 50
EXTERNAL_ID_MAX = 100
DATE_FORMATS = ["%Y/%m/%d", "%Y%m%d"]


def norm_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def to_timestamp(raw: str) -> int | None:
    """Return Unix seconds (UTC) for a date, ISO datetime or Unix timestamp; None if unparseable."""
    if raw.isdigit() and len(raw) > 8:  # 8 digits is a YYYYMMDD date
        value = int(raw)
        return value // 1000 if value > 10**11 else value  # milliseconds → seconds
    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
        for fmt in DATE_FORMATS:
            try:
                parsed = dt.datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return int(parsed.timestamp())


class RowBuilder:
    def __init__(self, ref: dict, external_sso: bool):
        self.ref = ref
        self.locales = {loc.lower(): loc for loc in ref["locales"]}
        self.currencies = set(ref["currencies"])
        self.timezones = set(ref["timezones"])
        self.external_sso = external_sso
        self.seen_emails: dict[str, int] = {}
        self.seen_external_ids: dict[str, int] = {}

    def country_code(self, raw: str) -> str | None:
        if len(raw) == 2 and raw.upper() in self.ref["countries"]:
            return raw.upper()
        return self.ref["countryAliases"].get(norm_key(raw))

    def build(self, line: int, values: dict[str, str]) -> tuple[dict[str, str], list[str], list[str]]:
        out = {column: "" for column in TEMPLATE}
        errors: list[str] = []
        warnings: list[str] = []

        email = values.get("email", "")
        if not email:
            errors.append("Missing email")
        elif not EMAIL_RE.match(email):
            errors.append(f"Invalid email format: {email}")
        out["email"] = email

        for field in ("firstName", "lastName"):
            out[field] = values.get(field, "")
            if len(out[field]) > NAME_MAX:
                warnings.append(f"{field} longer than {NAME_MAX} characters")

        raw_country = values.get("countryCode", "")
        country = self.country_code(raw_country) if raw_country else None
        if not raw_country:
            errors.append("Missing country")
        elif country is None:
            errors.append(f"Unknown country: {raw_country}")
        else:
            out["countryCode"] = country
        info = self.ref["countries"].get(country or "", {})

        raw_locale = values.get("locale", "")
        if raw_locale and raw_locale.replace("-", "_").lower() in self.locales:
            out["locale"] = self.locales[raw_locale.replace("-", "_").lower()]
        else:
            out["locale"] = info.get("locale") or DEFAULT_LOCALE
            if raw_locale:
                warnings.append(f"Locale {raw_locale} is not supported by Cleeng, used {out['locale']}")
            elif country and not info.get("locale"):
                warnings.append(f"No Cleeng locale for {country}, used {DEFAULT_LOCALE}")

        raw_currency = values.get("currency", "").upper()
        if raw_currency in self.currencies:
            out["currency"] = raw_currency
        else:
            out["currency"] = info.get("currency") or DEFAULT_CURRENCY
            if raw_currency:
                warnings.append(f"Currency {raw_currency} is not supported by Cleeng, used {out['currency']}")
            elif country and not info.get("currency"):
                warnings.append(f"No supported currency for {country}, used {DEFAULT_CURRENCY}")

        raw_tz = values.get("timezone", "")
        if raw_tz in self.timezones:
            out["timezone"] = raw_tz
        else:
            out["timezone"] = info.get("timezone") or ""
            if raw_tz:
                warnings.append(f"Unknown timezone {raw_tz}, used {out['timezone'] or 'the Cleeng default'}")

        for field in ("lastLogin", "createDate"):
            raw = values.get(field, "")
            if raw:
                stamp = to_timestamp(raw)
                if stamp is None or stamp <= 0:
                    warnings.append(f"Could not read {field} date {raw}, left empty")
                else:
                    out[field] = str(stamp)

        raw_ip = values.get("ipAddress", "")
        if raw_ip:
            try:
                out["ipAddress"] = str(ipaddress.ip_address(raw_ip))
            except ValueError:
                warnings.append(f"Invalid IP address {raw_ip}, left empty")
        if country in ("US", "CA") and not out["ipAddress"]:
            warnings.append("Missing IP address for a US/CA customer (needed for tax)")

        external_id = values.get("externalId", "")
        if external_id:
            if len(external_id) > EXTERNAL_ID_MAX:
                errors.append(f"externalId longer than {EXTERNAL_ID_MAX} characters")
            out["externalId"] = external_id
        elif self.external_sso:
            warnings.append("Missing externalId while the publisher uses external SSO")

        password_hash = values.get("passwordHash", "")
        if password_hash and not BCRYPT_RE.match(password_hash):
            warnings.append("passwordHash is not a bcrypt hash; password sign-in may fail")
        out["passwordHash"] = password_hash

        # Duplicates last, and only against rows that will be imported, so the
        # first importable occurrence wins.
        if not errors:
            key = email.lower()
            if key in self.seen_emails:
                errors.append(f"Duplicate email, first imported from row {self.seen_emails[key]}")
            if external_id and external_id in self.seen_external_ids:
                errors.append(f"Duplicate externalId, first imported from row {self.seen_external_ids[external_id]}")
        if not errors:
            self.seen_emails[email.lower()] = line
            if external_id:
                self.seen_external_ids[external_id] = line

        return out, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--map", action="append", default=[], metavar="FIELD=COLUMN")
    parser.add_argument("--full-name-column", help="Split this column on the first space into firstName and lastName")
    parser.add_argument("--external-sso", action="store_true", help="Warn on rows without externalId")
    parser.add_argument("--zip", action="store_true", help="Also write cleeng_migration_<date>.zip")
    args = parser.parse_args()

    try:
        with args.source.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            header = list(reader.fieldnames or [])
            rows = [(reader.line_num, row) for row in reader]
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        parser.error(f"cannot read {args.source}: {exc}")

    mapping = {}
    for pair in args.map:
        field, sep, column = pair.partition("=")
        if not sep or field not in TEMPLATE:
            parser.error(f"--map expects <cleengField>=<sourceColumn> with a field from {TEMPLATE}, got {pair!r}")
        if column not in header:
            parser.error(f"source column {column!r} not in file header {header}")
        mapping[field] = column
    if "email" not in mapping or "countryCode" not in mapping:
        parser.error("--map email=... and --map countryCode=... are required")
    if args.full_name_column and args.full_name_column not in header:
        parser.error(f"--full-name-column {args.full_name_column!r} not in file header {header}")

    builder = RowBuilder(json.loads(REFERENCE.read_text(encoding="utf-8")), args.external_sso)
    imported, flagged = [], []
    for line, row in rows:
        values = {field: (row.get(column) or "").strip() for field, column in mapping.items()}
        if args.full_name_column:
            first, _, last = (row.get(args.full_name_column) or "").strip().partition(" ")
            values.setdefault("firstName", first)
            values.setdefault("lastName", last.strip())
        out, errors, warnings = builder.build(line, values)
        if not errors:
            imported.append(out)
        if errors or warnings:
            flagged.append({
                "Row": line, **{column: row.get(column) or "" for column in header},
                "Issue Type": "Error" if errors else "Warning",
                "Issue Description": "; ".join(errors + warnings),
            })

    args.out_dir.mkdir(parents=True, exist_ok=True)
    import_path = args.out_dir / "cleeng_import.csv"
    with import_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TEMPLATE)
        writer.writeheader()
        writer.writerows(imported)
    files = [import_path]
    errors_path = args.out_dir / "migration_errors.csv"
    errors_path.unlink(missing_ok=True)
    if flagged:
        with errors_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["Row", *header, "Issue Type", "Issue Description"])
            writer.writeheader()
            writer.writerows(flagged)
        files.append(errors_path)
    if args.zip:
        zip_path = args.out_dir / f"cleeng_migration_{dt.date.today().isoformat()}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, path.name)
        files.append(zip_path)

    error_rows = [f for f in flagged if f["Issue Type"] == "Error"]
    summary = {
        "sourceRows": len(rows),
        "importRows": len(imported),
        "errorRows": len(error_rows),
        "warningRows": len(flagged) - len(error_rows),
        "files": [str(path) for path in files],
        "issues": [{"row": f["Row"], "type": f["Issue Type"], "description": f["Issue Description"]} for f in flagged[:50]],
        "issuesTruncated": len(flagged) > 50,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

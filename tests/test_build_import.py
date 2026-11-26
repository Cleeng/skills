import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills/cleeng-migration-assistant/scripts/build_import.py"
FIXTURES = ROOT / "tests/fixtures"
HEADER = "email,firstName,lastName,locale,countryCode,lastLogin,createDate,timezone,currency,externalId,ipAddress,passwordHash"


def run(test, source, *args):
    tmp = tempfile.TemporaryDirectory()
    test.addClassCleanup(tmp.cleanup) if isinstance(test, type) else test.addCleanup(tmp.cleanup)
    out = Path(tmp.name)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURES / source), "--out-dir", str(out), *args],
        capture_output=True, text=True,
    )
    return result, out


def read(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


class RecurlyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result, cls.out = run(
            cls, "recurly_accounts.csv",
            "--map", "email=email", "--map", "firstName=first_name", "--map", "lastName=last_name",
            "--map", "createDate=created_at", "--map", "countryCode=address.country",
            "--map", "currency=currency", "--map", "externalId=account_code", "--external-sso", "--zip",
        )

    def test_import_file_matches_cleeng_template(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        header = (self.out / "cleeng_import.csv").read_text().splitlines()[0]
        self.assertEqual(header, HEADER)
        rows = {row["email"]: row for row in read(self.out / "cleeng_import.csv")}
        self.assertEqual(set(rows), {"anna@example.com", "bob@example.com", "eve@example.com", "gina@example.com"})
        self.assertEqual(rows["anna@example.com"]["createDate"], "1680343200")
        self.assertEqual(rows["anna@example.com"]["locale"], "pl_PL")
        self.assertEqual(rows["anna@example.com"]["timezone"], "Europe/Warsaw")
        self.assertEqual(rows["eve@example.com"]["locale"], "en_US")
        self.assertEqual(rows["eve@example.com"]["createDate"], "")
        self.assertEqual(rows["gina@example.com"]["lastName"], "Kept")
        self.assertEqual(rows["gina@example.com"]["createDate"], "1683504000")

    def test_flagged_rows_keep_source_columns(self):
        issues = {row["Row"]: row for row in read(self.out / "migration_errors.csv")}
        self.assertEqual(
            {row: issue["Issue Type"] for row, issue in issues.items()},
            {"3": "Warning", "4": "Error", "5": "Error", "6": "Error", "7": "Warning", "8": "Error"},
        )
        self.assertEqual(issues["7"]["account_code"], "acc-6")
        self.assertTrue(any(f.endswith(".zip") for f in json.loads(self.result.stdout)["files"]))


class VimeoTest(unittest.TestCase):
    def test_names_split_and_countries_resolved(self):
        result, out = run(
            self, "vimeo_members.csv", "--map", "email=email", "--map", "countryCode=location.country",
            "--map", "createDate=joined_date", "--map", "lastLogin=last_login", "--full-name-column", "name",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = {row["email"]: row for row in read(out / "cleeng_import.csv")}
        maria = rows["maria@example.com"]
        self.assertEqual((maria["firstName"], maria["lastName"]), ("Maria", "Silva Santos"))
        self.assertEqual((maria["countryCode"], maria["locale"], maria["currency"]), ("BR", "pt_BR", "BRL"))
        self.assertEqual(rows["jean@example.com"]["currency"], "EUR")
        self.assertNotIn("solo@example.com", rows)


class ArgumentsTest(unittest.TestCase):
    def test_unknown_source_column_is_rejected(self):
        result, _ = run(self, "vimeo_members.csv", "--map", "email=mail", "--map", "countryCode=location.country")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()

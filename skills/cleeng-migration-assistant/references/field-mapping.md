# Field mapping

## Cleeng import columns

`scripts/build_import.py` writes these columns in this order. The Cleeng importer rejects a file whose header differs in any way.

| Field | Required | Accepted values | When missing |
|---|---|---|---|
| `email` | yes | valid email, unique in the file | row is an error |
| `firstName` | no | up to 50 characters | empty |
| `lastName` | no | up to 50 characters | empty |
| `locale` | yes | a Cleeng locale, see `assets/reference-data.json` | derived from country, else `en_US` |
| `countryCode` | yes | ISO 3166-1 alpha-2 | row is an error |
| `lastLogin` | no | Unix timestamp, seconds | empty |
| `createDate` | no | Unix timestamp, seconds | empty |
| `timezone` | no | IANA name, e.g. `Europe/Warsaw` | derived from country, else Cleeng default `Europe/Amsterdam` |
| `currency` | no | a Cleeng currency (32 ISO 4217 codes) | derived from country, else `EUR` |
| `externalId` | for external SSO | up to 100 characters, unique per publisher | empty |
| `ipAddress` | for US and CA | IPv4 or IPv6 | empty, warning for US and CA |
| `passwordHash` | no | bcrypt hash | empty |

## Mapping arguments

Pass one `--map <field>=<source column>` per mapped field. `email` and `countryCode` are required. Use `--full-name-column <column>` when the source has one name column; the script splits it on the first space.

The script accepts these source formats and converts them:
- country as a code (`us`, `US`) or an English name (`United States`, `Germany`, `UK`)
- dates as `YYYY-MM-DD`, ISO 8601 datetimes, `YYYY/MM/DD`, or Unix timestamps in seconds or milliseconds
- locale with `-` or `_` in any case (`en-gb` becomes `en_GB`)

Dates in other formats (for example `03/04/2021`) are left empty with a warning, because day and month order is ambiguous. Ask the publisher for the format and convert that column in a copy of the CSV before rerunning.

## Recurly

| Cleeng field | Recurly column |
|---|---|
| `email` | `email` |
| `firstName` | `first_name` |
| `lastName` | `last_name` |
| `countryCode` | `address.country` (or `country`) |
| `currency` | `currency`, if present |
| `createDate` | `created_at` |
| `externalId` | `account_code`, only for external SSO |

Recurly exports have no last login, IP address, timezone or password hash.

## Vimeo OTT

| Cleeng field | Vimeo column |
|---|---|
| `email` | `email` |
| `firstName`, `lastName` | `--full-name-column name` |
| `countryCode` | `location.country` (often a full country name) |
| `createDate` | `joined_date` |
| `lastLogin` | `last_login` |
| `externalId` | `user_id`, only for external SSO |

Vimeo exports have no currency, IP address, timezone or password hash.

Column names differ between export versions. Always map against the header of the uploaded file and confirm the mapping with the publisher.

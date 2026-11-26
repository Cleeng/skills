# Changelog

## Unreleased

- `cleeng-migration-assistant`: wizard that turns a Recurly or Vimeo OTT export into the Cleeng user-import CSV. `scripts/build_import.py` writes the importer's column order and Unix timestamps, maps locales and currencies to values Cleeng accepts, and lists rejected and flagged rows in `migration_errors.csv`.

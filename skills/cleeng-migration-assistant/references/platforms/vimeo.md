# Vimeo OTT export

## Steps

1. Sign in to the Vimeo OTT dashboard at `vimeo.com/ott` or the publisher's custom domain.
2. Open **Audience → Members**.
3. Click **Export Members**.
4. Choose format **CSV** and scope **All Members** (or filter by subscription status).
5. Click **Export**. The CSV downloads directly, or Vimeo emails a link for large exports.

## Common issues

- **Names are in one column.** Pass `--full-name-column name`; the script splits on the first space. If names are stored as "Last, First", ask the publisher and fix the column in a copy of the CSV first.
- **Countries are full names.** The script converts English country names such as "United States" to codes.
- **Several files arrive.** Ask for the files one at a time and run the build for each.
- **Some members have no country.** Those rows are excluded until the publisher supplies a country.

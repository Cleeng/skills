# Recurly export

## Steps

1. Sign in to the Recurly dashboard at `app.recurly.com`.
2. Open **Accounts** in the left navigation.
3. Click **Export** above the accounts list.
4. Choose export type **Accounts**, format **CSV**, and date range **All time** (or the range to migrate).
5. Click **Generate Export**. Recurly emails a download link, usually within a few minutes.
6. Download the CSV from that email.

## Common issues

- **The export email does not arrive.** Check the spam folder; the sender is `noreply@recurly.com`.
- **Several files arrive.** Recurly splits large exports. Ask for the files one at a time and run the build for each.
- **Some rows have no country.** Older Recurly accounts may have no address. Those rows are excluded until the publisher supplies a country.

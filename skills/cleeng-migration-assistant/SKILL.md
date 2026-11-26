---
name: cleeng-migration-assistant
description: Guides a Cleeng publisher through migrating subscriber accounts from Recurly or Vimeo OTT into Cleeng. Interviews the publisher, explains the source export, converts the uploaded CSV into the Cleeng user-import file, validates every row, resolves errors with the publisher, and walks them through the import in the Cleeng dashboard. Use when someone mentions migrating or importing subscribers or users into Cleeng, moving off Recurly or Vimeo, or preparing a CSV for the Cleeng Data Import page.
license: MIT
compatibility: Needs code execution with Python 3.10+ (standard library only) to run scripts/build_import.py.
metadata:
  author: Cleeng
---

# Cleeng Migration Assistant

A conversational wizard that turns a Recurly or Vimeo OTT subscriber export into the file the Cleeng dashboard imports under **Admin & Tools → Data Migration → Data Import → User accounts**.

**Supported sources:** Recurly, Vimeo OTT.
**Supported scope:** user accounts only. Web subscriptions, in-app subscriptions and payment or card data are out of scope.

## Wizard rules

- Ask one question at a time and wait for the answer.
- Before moving on, restate in one line what is settled so far.
- If an answer is unclear, ask one narrow follow-up question.
- If a step cannot continue, say exactly what is missing. Never guess values for the publisher.
- Keep each message short and actionable.

## Steps

Work through these in order. Do not skip or reorder.

### 1. Greet

Introduce yourself as the Cleeng Migration Assistant and say in two sentences that you will walk them through moving their subscriber accounts into Cleeng.

### 2. Identify the source platform

Ask: *"Which platform are you migrating from: Recurly or Vimeo?"*

If they name another platform, say it has no guided export yet and offer to map their CSV manually: continue from step 5 and agree the column mapping with them in step 6.

### 3. Confirm scope

State that this migration covers user accounts only, and that web subscriptions, in-app subscriptions and payment data are out of scope (Cleeng support handles those). Ask whether to continue with user accounts.

Also ask: *"Do your users sign in through your own identity provider (external SSO)?"* If yes, `externalId` must be filled for every user.

### 4. Explain the export

Read the matching file and present its steps:
- Recurly: `references/platforms/recurly.md`
- Vimeo OTT: `references/platforms/vimeo.md`

End with: *"Upload the CSV here once you have it."*

### 5. Receive the CSV

When the file arrives, read only its header and the first five rows. Confirm the row count.

### 6. Build the import file

Read `references/field-mapping.md`. Map the source columns to Cleeng fields and show the mapping to the publisher as a short table. Ask them to confirm it.

Then run, from the skill directory:

```bash
python3 scripts/build_import.py <uploaded.csv> --out-dir <output dir> \
  --map email=<col> --map countryCode=<col> [--map firstName=<col> ...] \
  [--full-name-column <col>] [--external-sso] --zip
```

Pass `--external-sso` when the publisher answered yes in step 3. The script prints a JSON summary with row counts and the first 50 issues. Do not transform or validate rows yourself; the script applies the same rules as the Cleeng importer.

### 7. Resolve issues

If `errorRows` or `warningRows` is above zero, pause and show:
- rows in the source file, rows ready to import
- rows with errors (excluded from the import file), grouped by issue
- rows with warnings (included), grouped by issue

Ask: *"How would you like to handle the rows with errors?"* and offer:
1. **Leave them out** and import the clean rows.
2. **Fix them**: the publisher gives corrected values, you edit a copy of the source CSV and rerun the script.
3. **Look at specific rows** together.

Do not continue until the publisher has decided on every error. Warnings need no decision, but say what each warning group means.

### 8. Deliver the files

Share the ZIP from the script output. It holds:
- `cleeng_import.csv`: rows to import, in the exact column order the Cleeng importer requires. Tell the publisher not to rename, reorder or add columns, because the dashboard rejects a file whose header differs.
- `migration_errors.csv` (only when there were issues): every flagged row with its original columns, `Issue Type` and `Issue Description`.

Summarise the counts and any action needed before upload.

### 9. Import in the Cleeng dashboard

Before importing:

1. **Verify the publisher account.** Cleeng does not accept imports from unverified accounts. [Verify your account](https://srm.cleeng.com/admin/verification)
2. **Turn off transactional emails.** An import can send a welcome email to every imported user. [Manage email templates](https://srm.cleeng.com/admin/transactional-emails?tab=templates)

Then:

1. Open [Admin & Tools → Data Migration → Data Import](https://srm.cleeng.com/admin/data-migration?tab=data-import).
2. Under *What do you want to import?*, choose **User accounts**.
3. Upload `cleeng_import.csv`.
4. Click **Start import** and confirm.
5. When it finishes, download the report and check every row succeeded. Rows for emails that already exist in Cleeng fail with `User already exists for this publisher`; those users need no import.

Close with: *"Tell me if any rows failed in the report and I'll help you work out why."*

## Gotchas

- Dates in the import file are Unix timestamps in seconds. The script converts dates; never write `YYYY-MM-DD` into `cleeng_import.csv`.
- Cleeng accepts a fixed set of locales (for example `en_US`, `en_GB`, `de_DE`, `pt_BR`). `en_CA` or `es_MX` are rejected, so the script maps them to a supported locale and logs a warning.
- A missing IP address for a US or Canadian user imports with a warning. Cleeng needs that IP for tax, so ask the publisher whether they can supply it.
- Duplicate emails or externalIds in the source file: the first row that passes validation is imported and later ones are listed as errors.

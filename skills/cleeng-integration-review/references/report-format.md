# Report format

Write the report in Markdown, in this order.

## Template

````markdown
# Cleeng integration review: <repository name>, <YYYY-MM-DD>

Scope: <folders reviewed, each marked client or server, with platform>. <N> files searched.
Integration: <integration types found, per folder>.
Rules checked against Cleeng guidance as of <the date at the top of api-surface.md>.

| Severity | Confirmed | Likely |
|---|---|---|
| Critical | 0 | 0 |
| High | 0 | 0 |
| Medium | 0 | 0 |
| Low | 0 | 0 |

## Findings

### <SEVERITY> · <RULE-ID> <rule title> · <Confirmed|Likely>

<path>:<line>[, <path>:<line> …]

```<language>
<the relevant lines, at most 8, credentials replaced by <redacted>>
```

**What the code does.** <one or two sentences about this codebase, not the generic rule>

**Why it matters.** <from the rule's Why, applied to this code>

**Fix.** <steps, then a code change in the codebase's language and style>

**Check** (Likely only). <what the user should verify to confirm or dismiss it>

**Source.** <the rule's Source link, or "Cleeng recommendation">

<repeat for each finding>

## JSON-RPC methods to replace

<only when ENV-02 is found: method, file:line, replacement>

## Coverage

| Rule | Result |
|---|---|
| AUTH-01 | Finding, Confirmed |
| AUTH-02 | Checked, no hits |
| HOOK-01 | Not applicable: no webhook receiver in this repository |
| … | … |

## Other observations

<only when you noticed problems outside the rules, such as general security or error-handling bugs near Cleeng code: one line each, with file:line. No severity.>

## Dashboard checklist

<the items from config-checklist.md that apply to the integration types found>

## Not covered

<what the review could not see: traffic volumes, systems outside this repository, folders skipped and why>
````

## Rules for the report

- Sort findings by severity (Critical, High, Medium, Low), then Confirmed before Likely, then rule ID.
- One finding per rule. List every location under it; above ten locations, list ten and give the total.
- Quote real lines from the codebase with their line numbers. Never invent code.
- Replace every credential, secret or token value with `<redacted>`, in excerpts and in prose.
- The coverage table has one row per rule ID from `rules-index.md`, in the same order. Never merge rules into a range such as "IAP-01 to IAP-06". Each row has one of: `Finding, Confirmed`, `Finding, Likely`, `Checked, no hits`, `Not applicable: <reason>`.
- Write fixes for this codebase: its language, HTTP client, state management and naming.
- Findings use rule IDs only. Put anything outside the rules under Other observations.
- Keep each finding short. The reader is the developer who owns the code.

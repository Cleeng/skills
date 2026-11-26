# Integration review fixtures

Small synthetic integrations for evaluating `cleeng-integration-review`. Each folder except `clean-reference` contains Cleeng integration problems at known lines; `EXPECTED.json` maps each fixture to the findings a review must report, as rule ID and file:line. A review may report more, and may cite another line in the same function.

| Fixture | Stack |
|---|---|
| `web-spa-direct` | React + TypeScript calling MediaStore API directly |
| `node-middleware` | Express backend on Core API 3.1, SSO, webhooks, JSON-RPC |
| `android-iap` | Kotlin, OkHttp, Google Play Billing |
| `tvos-swift` | Swift, URLSession, SwiftUI |
| `clean-reference` | A Node backend and web client that follow the rules |

## Running an evaluation

Copy a fixture out of this repository first, so the agent cannot read `EXPECTED.json`:

```bash
cp -r tests/fixtures/integrations/node-middleware /tmp/eval-node-middleware
cd /tmp/eval-node-middleware
claude --plugin-dir /path/to/skills -p "Review my Cleeng integration. Show the report here."
```

Do the same in a second agent with the skill installed. Compare each report with `EXPECTED.json`:

- every expected rule is reported, citing the expected file and a line in the same function;
- `clean-reference` produces no Confirmed findings;
- the coverage table lists every rule ID from `references/rules-index.md`.

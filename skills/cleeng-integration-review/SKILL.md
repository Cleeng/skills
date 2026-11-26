---
name: cleeng-integration-review
description: Reviews code that integrates with Cleeng (web app, mobile or TV app, backend) against Cleeng's integration recommendations and reports each finding with file:line, the reason and the fix. Covers API keys and tokens, sign-in and token refresh, call volume and caching, entitlement checks, timeouts and retries, webhooks, in-app purchases, sandbox settings and deprecated APIs. Use when someone asks to review, audit or check their Cleeng integration, cut the number of Cleeng API calls, fix 429 errors from Cleeng, check a webhook handler, or prepare an app for go-live or a large live event.
license: MIT
compatibility: Needs read access to the codebase and a text search tool (ripgrep, grep or the agent's own search). Makes no network calls.
metadata:
  author: Cleeng
---

# Cleeng Integration Review

Reads a codebase that calls Cleeng and checks it against Cleeng's integration rules. Each finding names the rule, the file and line, what the code does, why it matters and how to fix it.

## Ground rules

- Read only. Do not edit code unless the user says yes to a specific fix.
- Make no network calls, and never call Cleeng APIs. The review works from the code alone.
- Never print a credential you find. Quote the file and line, and replace the value with `<redacted>`.
- Report a finding as **Confirmed** only when you have read the code that shows the problem. Otherwise report it as **Likely**, and say what the user should check.
- Check every rule that applies, including after the first findings. The coverage table at the end must list every rule ID.

## Steps

### 1. Scope

Ask which folder to review if the user did not say. Then list the top-level folders and decide which hold client code (web, iOS, tvOS, Android, Roku, smart-TV apps) and which hold server code (backends, serverless functions, middleware, jobs).

If a folder could be either, ask the user one question about it. The client/server split decides several rules: a publisher token is fine on a server and a critical finding in a client.

### 2. Inventory

Read `references/api-surface.md`. Run its inventory searches over the scope, then write down:

- the integration type or types: hosted widgets, MediaStore SDK, MediaStore API direct, Core API 3.1 from a backend, In-App API, JSON-RPC 3.0, Webhook Management API;
- every Cleeng call site, as file:line, API, endpoint and credential;
- whether the codebase has a webhook receiver, in-app purchase code, an entitlement cache, a token store.

Tell the user in two or three lines what you found before going on.

### 3. Check each group

Read `references/rules-index.md` for the full rule list and the severity scale. Then, for each group that applies, read its reference file and work through every rule in it:

| Group | Read | Applies when |
|---|---|---|
| AUTH | `references/auth.md` | Always |
| SESS | `references/session.md` | Any customer sign-in, SSO, JWT or refresh token handling |
| LOAD | `references/call-volume.md` | Always |
| ENT | `references/entitlements.md` | Any access check or playback gating |
| RES | `references/resilience.md` | Always |
| HOOK | `references/webhooks.md` | A webhook receiver or webhook registration exists |
| IAP | `references/in-app-purchases.md` | Apple, Google Play, Amazon, Roku, Samsung or Vizio purchase code exists |
| ENV | `references/environments.md` | Always |
| WEB | `references/web-widgets-sdk.md` | Hosted widgets (`cleeng.js`) or `@cleeng/mediastore-sdk` are used |

For each rule:

1. Run the searches in its **Search** block, limited to the client or server folders it names.
2. Read the code around each hit, and follow calls one or two levels when the hit alone does not show the behaviour.
3. Apply its **Judge** block: Confirmed, Likely, or not a finding.
4. Record the result for the coverage table: finding, checked with no hits, or not applicable (with the reason).

### 4. Report

Read `references/report-format.md` and write the report in that format. Ask whether to save it as `cleeng-integration-review.md` at the repository root; otherwise show it in the chat.

### 5. Offer fixes

Offer to fix findings one at a time, starting with Critical. Before each edit, show the change and wait for a yes. After a fix, re-run that rule's searches to confirm the finding is gone.

# Workspace safety

Context: the guardrails for every call this skill makes into a Customer.io
workspace. Read it at BUILD stage 0 and LIVE-AUDIT step 1, and whenever a call
is not plainly a read. The order of the build is in `references/build-order.md`.

## Contents
- Choosing the workspace
- Sandbox or production
- Approval split by verb
- Dry run, then approval, then write
- Allowed calls
- The never list
- When something goes wrong

## Choosing the workspace
1. Call `cio_auth_status` and list `allowed_workspace_ids` to the user with
   each workspace's name from `GET /v1/environments/{environment_id}`.
2. Ask which workspace to use, every run, even when the conversation named one
   earlier: a session can hold several workspaces and the wrong one is the most
   expensive mistake BUILD can make.
3. Repeat the chosen ID and name back in the stage 0 summary. Every later call
   passes that ID explicitly in `params`; never rely on a default.
4. Workspace names can contain an operator's brand. Use them in the
   conversation only; never copy them into a deliverable, an object name or a
   description (hard rule 8).

## Sandbox or production
The API has no sandbox flag, so the environment is the user's statement,
checked against evidence. Ask "sandbox or production?" at intake, then read:
- the workspace name (words like sandbox, test, staging, beta, dev);
- `GET .../customers` `meta.pagination.total` (a handful of profiles suggests a
  sandbox; thousands suggests production);
- running automations in `GET .../campaigns` (`state == "running"`);
- `subscription_center_enabled` and `is_sample_workspace` on the environment.
If the evidence contradicts the user's answer (they said sandbox; the workspace
has running automations and thousands of profiles), stop and show the evidence.
For production, BUILD continues only after the user types the workspace ID back
as confirmation, and the dry-run previews say "PRODUCTION" in their heading.

## Approval split by verb
The official server splits the API by HTTP verb so the connector can treat each
differently:
| Tool | Verb | This skill |
|---|---|---|
| `cio_read_api` | GET | Used freely for reads; may be always-allowed in the connector |
| `cio_write_api` | POST, PUT, PATCH | BUILD stages 2-8 and smoke steps S5-S7 (`smk-<run>-` profiles only) only, each call after a dry run and the user's approval of that stage |
| `cio_delete_api` | DELETE | Never called |
A read that the API exposes as a POST (for example `attributes/profile_count`)
is not used, because it would go through the write tool; use the GET
equivalents in `references/build-order.md`.

## Dry run, then approval, then write
1. Build every request of a stage and send each with `dry_run: true`.
2. Show the user one preview block per stage: for each request, the verb, the
   path, the object name and the fields that matter (conditions, trigger, exits,
   topic, limit, `sending_state`). Put creates and approved updates in separate
   lists; reused objects are listed as "found, not changed".
3. Wait for an explicit approval of that stage ("approve stage 4"). Approval of
   one stage never carries over to the next.
4. Execute the approved requests exactly as previewed. Any change after the
   preview needs a new preview.
5. Read back each created object and record its ID and state in the build sheet.
When the run is a test, or the user asked for dry run only, stop after step 2 of
each stage, write the build sheet with `Customer.io ID` = `dry-run` and state
`planned`, and move to the next stage.

## Allowed calls
- Reads listed in `references/build-order.md` and `protocols/live-audit.md`.
- Creates: subscription topics, snippets, data-driven segments, frequency
  caps, webhook configurations, reporting webhooks with `enabled: false`,
  automations (draft) and their actions; per-action topic assignment through
  `PUT .../subscription_topic_messages/update` on actions this run created.
- Updates, only on objects this run created, or on existing objects the user
  approved by name: automation `recipients`, `conversion`, `exit_conditions`,
  `add_actions`, `global_settings`; a snippet value; a segment's conditions.
- Smoke profiles (SKILL.md hard rule 9, `protocols/smoke.md`):
  `POST .../customers` and `PUT .../customers/{customer_id}`, only for IDs
  that start with `smk-<run>-` of the current run, with no email, phone or
  device.

## The never list
Each line names the call so it can be recognised in a plan.
- Automation state: no `update_type: "state"` at all (`start`, `restart`,
  `schedule`, `stop`, `sunset`, `archive`, `unarchive`). Activation and
  retirement belong to the user.
- Sending: no `sending_state: "automatic"`; no `POST .../events`; no
  `POST .../verify/*` test sends; no `POST .../actions/{action_id}/test`; no
  `POST .../campaigns/{campaign_id}/triggers` (fires a broadcast); no
  newsletter sends; no enabled reporting webhook.
- People: no `customers` writes (create, update, delete, merge, subscribe,
  unsubscribe, unsuppress, optouts); no `PUT .../segments/{segment_id}/members`;
  no `suppress` (SKILL.md hard rule 1). One exception (SKILL.md hard rule 9):
  `POST .../customers` and `PUT .../customers/{customer_id}` for `smk-<run>-`
  IDs only, after a dry run and approval; never a delete, merge or
  subscription change, and never any other profile.
- Deletion: no `DELETE` on anything, and no `segments/delete`,
  `segments/archive` or `delete_actions` on objects the user did not ask to
  change; `?force=true` never.
- Workspace: no `PUT .../settings/workspace`, no `PUT .../message_limits`
  (deprecated), no signing-secret rotation, no subscription center settings.
- Secrets: never ask for or repeat a header value or token; create webhook
  configurations without secret headers and have the user add them in the app;
  never read `GET .../webhook_configurations` (decrypted headers).

## When something goes wrong
- A write returns an error: read the message, fix the structure, and re-preview.
  If only the response handling failed, read the object first; the write may
  have landed, and re-sending `add_actions` creates duplicate actions.
- A `409` on an automation means wrong state or an edge-count mismatch, never a
  reason to delete and recreate.
- The data-driven segment allowance is reached: stop, relay the platform's limit
  message as written, and ask. Never substitute a manual segment.
- Anything that would need a never-list call: stop and hand the user the exact
  step to do in the app.

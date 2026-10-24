# Build sheet: [[SCOPE]]

Workspace: [[WORKSPACE_ID]] ([[sandbox|production]])
Run: [[dry run|live]]
Design: [[DESIGN_FILE]]
Pre-flight: stage [[N]] [[GO|NO-GO]]: [[READ_AND_OBSERVED_VALUE]]
[[ONE_PRE_FLIGHT_LINE_PER_STAGE_1_TO_8B]]
[[ONLY_WHEN_A_STAGE_STOPPED_THE_BUILD: Stopped at stage N: reason]]
Smoke report: [[SMOKE-REPORT.md_VERDICT_OR_REASON_FOR_SKIPPING]]

The Pre-flight lines come from build stage 0b, one per checked stage, and stay
on the final sheet. The Smoke report line names `SMOKE-REPORT.md` (a separate
file beside this sheet) with its verdict, or the user's reason for skipping.
Use this exact table structure: `scripts/validate_build_sheet.py` reads it.
One row per object and per message action, in stage order. Result is
`created`, `existing` (found by name and reused) or `planned` (not yet written:
the stage 0 plan, or a dry run; Customer.io ID `dry-run`). State is the state
read back after the write; on a `planned` row it is the target state the write
will produce. Automations `draft` (or `paused` / `stopped` if the user changed
them), message actions `draft` (their `sending_state`), reporting webhooks
`disabled`, segments `complete`, other objects `active`. The Limit column holds
the frequency cap. Topic, Limit and Exit conditions are `-` on rows that are
neither automations nor message actions. A marketing automation names its
default topic spec ID and ID, its frequency cap spec ID and ID, and
`RG_EXIT_BLOCK` with the `SEG_RG_SUPPRESSED` ID; each of its message actions
names its own topic. A non-marketing automation names `TOP_SAFER_GAMBLING` or
`TOP_TRANSACTIONAL` and Limit `none`. A build that stopped keeps the table
header with no rows and lists everything under "Not built".

## Objects
| Stage | Spec ID | Type | Name | Customer.io ID | Result | State | Topic | Limit | Exit conditions | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | [[TOP_ID]] | subscription_topic | [[PLAYER_FACING_NAME]] | [[ID]] | [[RESULT]] | active | - | - | - | description: [[TOP_ID]]; opt_in [[true|false]] |
| 3 | [[SNP_ID]] | snippet | [[snippet_name]] | [[ID]] | [[RESULT]] | active | - | - | - | [[VALUE_SOURCE]] |
| 4 | [[SEG_ID]] | segment | [[SEG_ID]] | [[ID]] | [[RESULT]] | complete | - | - | - | count [[N]] |
| 6 | [[LIM_ID]] | frequency_cap | [[LIM_ID]] | [[ID]] | [[RESULT]] | active | - | - | - | [[RULES]] |
| 7 | [[WHK_ID]] | reporting_webhook | [[WHK_ID]] | [[ID]] | [[RESULT]] | disabled | - | - | - | [[EVENTS]] |
| 8 | [[JRN_ID]] | automation | [[JRN_ID]] | [[ID]] | [[RESULT]] | draft | [[TOP_ID]] ([[ID]]) | [[LIM_ID]] ([[ID]]) | RG_EXIT_BLOCK (SEG_RG_SUPPRESSED [[ID]]) | [[TRIGGER]] |
| 8 | [[JRN_ID]]#[[STEP]] | message_action | [[STEP]] Email: [[PURPOSE]] | [[ID]] | [[RESULT]] | draft | [[TOP_ID]] ([[ID]]) | same as automation | - | [[GATE_CODE]]; L3 and L4 |

## Data-model check (stage 1)
Present: [[ATTRIBUTES_AND_EVENTS_PRESENT]]
Missing: [[MISSING_OR_NONE]]
Operator field mapping (confirmed by the user): [[OPERATOR_FIELD_TO_CANONICAL_OR_NONE]]

## Not built
[[OBJECTS_SKIPPED_WITH_REASON_OR_NONE]]

## Mechanics to verify in the workspace
[[ITEMS_MARKED_VERIFY_IN_WORKSPACE]]

## Activation checklist (the user's; nothing was started or sent)
- [ ] Smoke report: PASS (`SMOKE-REPORT.md`), or each WARN accepted by name, or the recorded reason for skipping; start nothing on FAIL.
- [ ] Add the bearer token header to `WHK_L4_VERIFY_SUPPRESSION` in the app.
- [ ] Confirm in the app that each marketing automation's exit panel shows the RG exits as one OR group.
- [ ] Author and review every email: sender, subject, unsubscribe and preference links, footer snippets.
- [ ] Flip emails from draft to automatic in the app, not via `PUT /actions/{id}` (it replaces the whole action and blanks a per-email topic); otherwise re-check `subscription_topic_messages/list`.
- [ ] Run the gate QA cases (QA reference) with a self-excluded test player; zero marketing received.
- [ ] Switch message actions from draft to automatic only after review.
- [ ] Enable `WHK_REPORTING_COUNTER_FEED` once the backend endpoint is live.
- [ ] Start each automation yourself; reactivation and win-back journeys without backfill (future additions only).
- [ ] Compliance and marketing operations sign-off recorded.

# Rollback list
Fill from `templates/rollback-list.md` here, or keep it in its own file and pass
it to the validator with `--rollback`. Every `created` row above appears in it.

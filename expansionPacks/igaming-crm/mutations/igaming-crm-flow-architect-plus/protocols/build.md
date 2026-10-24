# Protocol: build

Context: runs after intake-plus chose BUILD and a design for the requested
scope passes `protocols/self-check.md`. It creates that design's objects in the
chosen Customer.io workspace in dependency order, leaves every automation in
draft, and hands activation to the user. Freedom is low here: the order, the
previews and the checks do not change between runs.

## Contents
- Mission
- Steps: the checklist, then stages 0-10 (workspace, readiness pre-flight
  and planned sheet, data-model check, topics, snippets, gate segments,
  lifecycle segments, frequency caps, webhooks, automations, smoke test,
  build sheet, activation checklist)
- Guidelines
- Next

## Mission
Every object in scope exists exactly once in the workspace, named with its spec
ID, wired to the gate, inert until the user activates it, and listed in a build
sheet that passes `scripts/validate_build_sheet.py`, with a rollback list beside it.

## Steps
Copy this checklist into the reply and tick it off. Read
`references/build-order.md` before stage 0 and the Customer.io skills it names
before each stage's first write. Every write follows the cycle in
`references/workspace-safety.md` ("Dry run, then approval, then write"); a
dry-run-only run stops each stage after the preview and records `planned` rows.
If a check fails, return to stage N, where N is the stage that produced the
object (or to DESIGN, when the spec itself is wrong), fix it there, and re-run
the stages after it; find-by-name keeps the re-run from duplicating anything.
A stage that stops the build (stage 1 missing gate attributes, stage 2 with the
subscription center off, an allowance or channel refusal) writes the line
`Stopped at stage N: <reason>` at the top of the build sheet, keeps every object
not built under "Not built", and goes straight to stages 9 and 10. The
stage 0b pre-flight finds these blockers before any write; the build still
stops at the first failing stage, but the user sees the whole list up front.

When the user asked for a "paused" automation, say once that Customer.io
creates automations in `draft` and an automation reaches `paused` only after
someone starts it; starting belongs to the user (hard rule 1), so the build
delivers `draft` with every message action `sending_state: "draft"`, the inert
equivalent.

```text
Build progress:
- [ ] 0 Workspace, auth, cio_prime, workspace facts
- [ ] 0b Readiness pre-flight (reads only), planned sheet validated
- [ ] 1 Data-model check and operator field mapping
- [ ] 2 Subscription topics
- [ ] 3 Snippets
- [ ] 4 Gate and suppression segments
- [ ] 5 Lifecycle, trigger and cap segments
- [ ] 6 Frequency caps
- [ ] 7 Webhook configurations and reporting webhooks
- [ ] 8 Automations in draft
- [ ] 8b Smoke test (protocols/smoke.md), or the user's reason for skipping
- [ ] 9 Build sheet validated, rollback list written
- [ ] 10 Activation checklist handed to the user
```

0. **Workspace.** Call `cio_auth_status`; confirm the
   workspace ID the user chose at intake is in `allowed_workspace_ids` and
   repeat its ID and name back. Call `cio_prime`; read only the section
   headings of recipes/diagnosing_workspace_health.md and
   `GET .../health` (`alerts`), and read the recipe section for an alert
   only if one fires. Read `GET /v1/environments/{environment_id}` (name,
   `subscription_center_enabled`) and `GET .../settings/workspace`
   (data-driven segment allowance). Run the sandbox-or-production check in
   `references/workspace-safety.md`. Done when the user has confirmed
   workspace and environment in this run.
0b. **Readiness pre-flight and planned sheet.** Before any write, check every
   later stage's gate with GET reads only (list and rules:
   `references/build-order.md`, "Readiness pre-flight"): the 14 gate
   attributes of stage 1 present, populated on the sample and carrying
   canonical values, with the proposed field mapping (when the user supplies
   a gate-readiness pack output from a workspace-specific data-analyst
   skill, take that table for the stage 1 row instead of re-deriving it,
   under the rules in `references/data-packs.md`); for stage 2
   `subscription_center_enabled` and the topic count; for stage 3 that
   `GET .../snippets` answers; for stages 4-5 the data-driven segment
   allowance against the segments the plan creates; for stage 6
   `GET .../frequency_cap_supported_channels` against the scoped caps; for
   stage 7 that `GET .../webhook_configurations_minimal` and
   `GET .../webhooks` answer (a 403 is NO-GO); for stage 8b `identifier_type`
   and `delivery_settings`. Show one table, `| Stage | Gate | Read | Observed
   | Verdict | Fix and owner |`, with every blocker at once and a verdict GO
   or NO-GO per stage. Each stage still runs its own check when it is
   reached, because the workspace can change in between. Write the planned
   build sheet from `templates/build-sheet.md`: one `Pre-flight: stage N GO|NO-GO: <reason>`
   line per checked stage under the header lines, then every topic, snippet,
   segment, frequency cap, webhook, automation and message action the design
   needs, Result `planned`, Customer.io ID `dry-run`, State the target state.
   A NO-GO does not remove rows from the plan; the build runs up to the first
   NO-GO stage and stops there as described above. Run
   `python3 scripts/validate_build_sheet.py PLANNED-SHEET.md` and fix the plan
   until it exits 0, so a plan that breaks a rule is caught before any write.
   Done when the pre-flight table is shown, the planned sheet with its
   Pre-flight lines exits 0, and the user has confirmed the planned rows.
1. **Data-model check and mapping.** Read `GET .../attributes` (names under
   `.attributes[].id`), one page of `GET .../customers` and the attributes of
   up to five sampled profiles (`GET .../customers/{customer_id}`), and
   `GET .../event_names`. Compare with every attribute and event the scoped
   segments, triggers, exits and preconditions read (`references/data-model.md`,
   `references/event-taxonomy.md`). Report present, missing, and present but
   never populated on the sample. For each missing canonical name, look for an
   operator field that may carry the same fact (for example `account_state`
   for `account_status`, `marketing_allowed` for `email_marketing_consent`)
   and propose the mapping table of `references/data-model.md` ("Mapping
   operator field names": operator field, canonical attribute, transform). A
   mapping counts only once the user confirms it; the backend then sends the
   canonical attribute, because segment logic never mixes both names. If any
   gate attribute of `RG_EXIT_BLOCK` or `SEG_CAN_RECEIVE_MARKETING` is still
   missing (`marketing_blocked`, `self_excluded`,
   `self_exclusion_register_match`, `timeout_active`, `rg_risk_level`,
   `account_status`, `aml_status`, `unsubscribed`, `email_marketing_consent`,
   `email_verified`, `age_verified`, `kyc_status`, `country_license_status`,
   `fraud_flag`), stop the build with `Stopped at stage 1: <missing list>`: a
   negated condition on an attribute the backend never sends matches
   everyone, so the gate would pass every player. Done when the report and
   the proposed mapping are shown and either no gate attribute is missing or
   the build has stopped.
2. **Subscription topics.** If `subscription_center_enabled` is `false`, stop
   with `Stopped at stage 2: subscription center off` and ask the user to
   enable it in the app (verify in workspace). List
   `GET .../subscription_topics`; find each scoped topic by its description
   prefix (`references/object-naming.md`). Preview creates for the missing ones
   with `opt_in: true` for the four marketing topics and `opt_in: false` for
   Safer Gambling and Transactional (`references/subscription-topics.md`); a
   topic's default cannot be changed after creation, so the preview names it.
   A journey whose topic depends on the product needs both product topics.
   Done when every scoped topic has an ID in the build sheet.
3. **Snippets.** List `GET .../snippets`; for each scoped snippet
   (`references/liquid-patterns.md`, referenced as `{{ snippets.name }}`)
   reuse, or preview a create with the value from intake or
   `references/markets.json`. A helpline or register you cannot verify keeps
   its `(verify before deployment)` marker in the build sheet Notes. Done when
   every scoped snippet has an ID.
4. **Gate and suppression segments.** Before each create, re-read
   `GET .../settings/workspace`; on an allotment of 0 stop and ask the user
   to confirm the segment entitlement before creating (its meaning is not
   yet proven; `references/build-order.md`). Find by name with
   `size` and `search`. Build each from `references/segment-library.md` as a
   data-driven segment, writing every condition as attributes (no references
   to other segments where the library allows attributes), because segment
   nesting is one level deep and a segment used as a trigger cannot later gain
   segment references. Order: `SEG_CAN_RECEIVE_MARKETING`,
   `SEG_CAN_RECEIVE_TRANSACTIONAL`, the suppression family
   (`SEG_RG_SUPPRESSED`, `SEG_SELF_EXCLUDED`, `SEG_TIMEOUT_ACTIVE`,
   `SEG_AML_RESTRICTED`, `SEG_UNSUBSCRIBED`, `SEG_COUNTRY_NOT_LICENSED`,
   `SEG_UNDERAGE_RISK`), then `SEG_FREQUENCY_CAP_REACHED`,
   `SEG_CAN_RECEIVE_BONUS` and `SEG_BONUS_ABUSE_SUPPRESSED` when in scope.
   After creation poll `GET .../segments/{segment_id}/status` until `complete`
   and record `GET .../segments/{segment_id}/count`. Done when every gate
   segment in scope is `complete` with its ID and count in the build sheet.
5. **Lifecycle, trigger and cap segments.** Same cycle as stage 4 for the
   segments the scoped journeys trigger on, branch on or cap by. A segment that
   references a gate segment may reference only leaf segments; otherwise inline
   the gate's conditions. Done when every scoped segment is `complete` with ID
   and count.
6. **Frequency caps.** Read `GET .../frequency_cap_supported_channels` and
   `GET .../frequency_caps`; read `GET .../message_limits` only to report a
   legacy `Default` cap, never to write it. A scoped frequency cap whose
   channel the workspace does not support (for example `LIM_SMS_MKT_WEEKLY`
   where only email and webhook are listed) is not created: record it under
   "Not built" with the reason, flag every marketing step on that channel as
   unbuildable, and leave those steps out of stage 8. Preview each remaining
   frequency cap from `references/caps-and-priority.md` with its rules in
   seconds (1 day = 86400, 7 days = 604800) and `retry_window_secs` of at most
   86400. If the API refuses two email rules in one frequency cap, stop and ask
   (verify in workspace). Done when every buildable frequency cap has an ID.
7. **Webhooks.** For the L4 pre-send check, find or create the webhook
   configuration `WHK_L4_VERIFY_SUPPRESSION` (URL from intake, method POST, no
   secret headers; the user adds the bearer token in the app). For the counter
   feed, find or create the reporting webhook `WHK_REPORTING_COUNTER_FEED` with
   `enabled: false` and the events of `references/event-taxonomy.md` ("Webhooks
   Customer.io sends back"). Done when both have IDs and the secret and enable
   steps are on the activation checklist.
8. **Automations in draft.** For each scoped journey, in catalogue order, follow
   the per-automation write order in `references/build-order.md`: create; set
   the trigger; goal, then exits as one `or` group; add every action and edge
   in one request; global settings with the default topic and the frequency
   cap; per-message topics; read back. For MKT_ and VIP_ journeys, check
   before the create that all three exist, or do not create the journey (hard
   rule 6): the `RG_EXIT_BLOCK` exit conditions with the `SEG_RG_SUPPRESSED`
   ID, the topic IDs, and the frequency cap ID. Each marketing email gets the
   L3 precondition (in `SEG_CAN_RECEIVE_MARKETING`, not in
   `SEG_FREQUENCY_CAP_REACHED`; bonus emails in `SEG_CAN_RECEIVE_BONUS`) and is
   preceded by the L4 webhook action and a true/false branch on the saved
   answer, with false, missing or error routed to its own exit (capture
   fields: verify in workspace). Topics come from the design's email rows:
   where the topic depends on the product, add the product split before the
   email and give each email variant its own topic (Casino Offers or
   Sportsbook Offers) through `PUT .../subscription_topic_messages/update`;
   the automation-level topic is the default for actions without an
   override. Actions are named by flow-table step (`references/object-naming.md`).
   Every message action is created with `sending_state: "draft"` and no
   content; content belongs to the user or the design-studio skill. Every
   Wait Until carries its Max time. RG, TXN, SVC and SYS journeys get their
   non-marketing topic and no frequency cap. Done when every scoped automation
   reads back in state `draft` with trigger, exits, topics and frequency cap as
   specified, and `GET .../campaigns/{campaign_id}/validate` shows no Liquid
   error.
8b. **Smoke test.** Run `protocols/smoke.md` (S1-S8) on the gate segments
   and the draft automations just built: by default in a sandbox, in
   production only on the confirmation in its S1. It writes
   `SMOKE-REPORT.md` beside the build sheet and parks its `smk-` profiles.
   A FAIL returns to the stage that made the object (4-5 for segments, 8 for
   automations). Done when the smoke verdict is recorded, or the user's
   reason for skipping it is written in the build sheet.
9. **Build sheet.** Update the planned sheet: one row per object and per
   message action, with read-back IDs and states, then run
   `python3 scripts/validate_build_sheet.py BUILD-SHEET.md`. Fill
   `templates/rollback-list.md` from the `created` rows in the reverse order of
   `references/rollback.md`, in the same file under `# Rollback list` or in a
   file passed with `--rollback`; the validator checks that every `created`
   row is on it. Parked smoke profiles go on the rollback list under
   "Smoke profiles: remove in the app". Exit 1: return to stage N for each finding (N in the row's
   Stage cell, or the stop stage), fix it, and re-run; exit 2: fix the path.
   For a long or production build, have a fresh-context subagent compare the
   read-backs with the sheet before reporting. Done when the validator exits 0.
10. **Activation checklist.** Hand the user the checklist in the build sheet,
    whose first line is "Smoke report: PASS" (or each WARN accepted by name,
    or the recorded reason for skipping; start nothing on FAIL); then:
    add the L4 bearer token; confirm in the app that each marketing
    automation's exit panel shows the RG exits as one OR group; author and
    review each email (sender, unsubscribe link, footer snippets); run the gate
    QA cases in `references/qa-launch.md` with the self-excluded test player;
    flip message actions from draft to automatic only after review, and do it
    in the app, not with `PUT /actions/{id}` (that call replaces the whole
    action and silently blanks a per-email topic), or re-check
    `subscription_topic_messages/list` afterwards; enable the
    reporting webhook; start each automation themselves, reactivation and
    win-back journeys without `backfill` so only future additions enter;
    compliance sign-off. Done when the checklist is delivered and the reply
    says that nothing was started or sent.

## Guidelines
- Pattern: one preview block per stage, creates and reused objects in separate
  lists, so the user approves a stage in one reading.
- Pattern: read back after every write; a 200 from this API is not proof (a
  silently ignored field also returns 200).
- Anti-pattern: building a journey before its gate segment reads `complete`;
  partial membership lets ineligible players through.
- Anti-pattern: fixing a wrong object by deleting and recreating it. Report it,
  correct it in place while it is a draft, or leave removal to the user.

## Next
Run `protocols/self-refine.md` at the end of the session. When the user asks
for a check of what was built, run `protocols/live-audit.md` on the same
workspace.

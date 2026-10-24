# Protocol: smoke

Context: runs as BUILD stage 8b (`protocols/build.md`), after the automations
read back in draft and before the build sheet, or on its own as SMOKE mode on
any workspace, for example after a LIVE-AUDIT. In a sandbox it runs by default
inside BUILD; in production it is offered and runs only on the confirmation in
S1. SKILL.md hard rule 9 is the only permission it has to write people, and
only `smk-<run>-` profiles.

## Contents
- Mission
- Steps: the checklist, then S1-S8
- Next

## Mission
Show, with a few synthetic profiles, that the gate segments put each
kind of player on the right side, and that each draft marketing automation
would admit the eligible player and refuse the suppressed one, without
starting, sending or deleting anything. It answers "does the wiring work?"; it
does not replace the manual QA matrix in `references/qa-launch.md` (deliveries,
the L4 endpoint, rendering, unsubscribe and SLA cases stay manual).

## Steps
Copy this checklist into the reply and tick it off:
```text
Smoke progress:
- [ ] S1 Workspace, environment, identifier type, delivery setting
- [ ] S2 Role map: which segment plays each gate role
- [ ] S3 Structural checks (no profiles needed)
- [ ] S4 Case plan and collision pre-flight
- [ ] S5 Create profiles (dry run, approval, write)
- [ ] S6 Observe memberships; run the change case
- [ ] S7 Park profiles; rollback entries
- [ ] S8 Smoke report and verdict
```

S1. **Workspace.** Hard rule 2 and the sandbox-or-production check in
`references/workspace-safety.md`. Read `GET /v1/environments/{environment_id}`:
`identifier_type` and `delivery_settings`. If `identifier_type` is `email`,
smoke profiles would need an address: stop and ask; never invent one. Report
`delivery_settings` (`send_to_one` or `off` is the safe sandbox setting). In
production, run only when the user types the workspace ID back and says
"smoke test in production"; every preview heading says PRODUCTION.

S2. **Role map.** Take segment IDs from the build sheet: `SEG_CAN_RECEIVE_MARKETING`,
`SEG_RG_SUPPRESSED`, `SEG_CAN_RECEIVE_TRANSACTIONAL`, `SEG_CAN_RECEIVE_BONUS`.
On a workspace this skill did not build, ask which existing segment plays each
role and record the answer; a role with no segment is a finding, and its cases
are CAN'T CHECK. Use the workspace's own attribute names from build stage 1
(for example `marketing_consent` for `email_marketing_consent`). Every role
segment must read `state: finished` before S5.

S3. **Structural checks**, from reads only; each is a STRUCT row in the report:
- each role segment's conditions say what the role means. An attribute
  condition reads back as `type: "attribute_change"` with a `to`/`from` pair;
  it is a current-value check, not change history (Customer.io skill fly-api/segment_conditions.md,
  "Attribute change"), so never report it as one. Flag instead a condition on
  an attribute missing from the data index, and a negative written as
  "equals false" where "is not true" is meant (a profile with no value escapes
  it; G8 and G10 test this);
- each draft MKT/VIP automation: state `draft`; every message action
  `sending_state: "draft"`; trigger includes `SEG_CAN_RECEIVE_MARKETING`; exits
  include the `RG_EXIT_BLOCK` attributes and the `SEG_RG_SUPPRESSED` ID; every
  marketing email has the L3 precondition (bonus emails `SEG_CAN_RECEIVE_BONUS`)
  and is preceded by the L4 webhook and its branch; topic and frequency cap set;
- each draft or scheduled broadcast: `send_to_everyone` false and the audience
  requires `SEG_CAN_RECEIVE_MARKETING`.

S4. **Case plan and collision pre-flight.** Run ID `YYYYMMDD-HHMM`. Profile ID
`smk-<run>-<case>` (lowercase), attributes `smoke_test: true`,
`smoke_run: <run>`, and the case's gate attributes, each set explicitly
(`true` or `false`, never omitted except in G10). No email, phone, device or
event, and no lifecycle attribute except what a journey case needs.

Gate cases (always; G1's attributes satisfy every gate condition):
| Case | Setup | Expected |
|---|---|---|
| G1 eligible | all gate conditions pass | in MARKETING and TRANSACTIONAL; not in RG_SUPPRESSED |
| G2 self-excluded | G1 + `self_excluded: true` at creation | not in MARKETING; in RG_SUPPRESSED; in TRANSACTIONAL |
| G3 register match | G1 + `self_exclusion_register_match: true` | as G2 |
| G4 timeout | G1 + `timeout_active: true`, `excluded_until` 7 days ahead | not in MARKETING; in RG_SUPPRESSED |
| G5 high risk | G1 + `rg_risk_level: "high"` | not in MARKETING; in RG_SUPPRESSED |
| G6 medium risk | G1 + `rg_risk_level: "medium"` | in MARKETING; not in BONUS |
| G7 kill switch | G1 + `marketing_blocked: true` | not in MARKETING |
| G8 no consent | G1 + consent `false` | not in MARKETING; in TRANSACTIONAL |
| G9 unsubscribed | G1 + `unsubscribed: true` | not in MARKETING |
| G10 missing value | G1 with `self_excluded` omitted | PASS if not in MARKETING; WARN if in it (a missing value passes `!= true`; the backend must always send it) |
| G11 change | G1, then after membership is confirmed update `self_excluded: true` | leaves MARKETING, enters RG_SUPPRESSED; record seconds; FAIL over 300 s |
A case whose attribute does not exist in the workspace is CAN'T CHECK and a
finding. G2 and G11 together show that membership follows the value whether it
was set at creation or changed later.

Journey cases, a pair per draft MKT/VIP automation in scope: J`<id>`-ok is G1
plus attribute values that satisfy the trigger's other conditions; J`<id>`-se
is the same plus `self_excluded: true`. Expected: ok is in the automation's
backing segment (`backing_segment_id`, a hidden segment that Customer.io keeps
built even while the automation is a draft), se is not. A trigger condition
an attribute cannot satisfy (performed an event, a time window on an event)
makes the pair CAN'T CHECK; never send an event to satisfy it.

Pre-flight: list running automations (`state: running`) and scheduled or
sending broadcasts; read each trigger, filter and audience; for every planned
profile, at S5 and again for the S6 update and the S7 parking values, decide
whether it could match (a condition on an attribute the profile lacks does not
match). In production, drop any profile that a running automation or
scheduled broadcast could admit and mark its case CAN'T CHECK (stop if it is
G1 or G2); in a sandbox, show the match and ask. Cap: 20 profiles per run;
more needs the user's approval. Show the plan and the pre-flight result before
any write.

S5. **Create.** One stage under the cycle in `references/workspace-safety.md`:
dry-run every `POST .../customers` (`{"customer": {"attributes": {"id": ...}}}`),
show one preview block, wait for "approve smoke profiles", write, read each
back with `GET .../customers/{customer_id}` and confirm the attributes landed.
Read the Customer.io skill fly-api/customers.md first (hard rule 4).
Never write to any profile whose ID does not start with `smk-<run>-`.

S6. **Observe.** Poll `GET .../customers/{customer_id}/segments` every 30 s, up
to 10 minutes, until every expected segment shows `state: finished` and
`members_out_of_date: false`; record seconds from write to the final state.
Whether that list includes hidden backing segments is to be confirmed in the
workspace (verify in workspace); if not, mark the journey pairs CAN'T CHECK
rather than inferring from segment counts. Then run G11 with
`PUT .../customers/{customer_id}` after its own preview and approval, and time
it the same way.

S7. **Park.** Preview, approve, then update every smoke profile of the run
to `marketing_blocked: true` and `unsubscribed: true` (re-check the pre-flight
for these values first). List every `smk-<run>-` ID in the rollback list under
"Smoke profiles: remove in the app (People, search smk-)". Never delete them;
a re-run uses a new run ID and leaves older parked profiles alone.

S8. **Report.** Write `SMOKE-REPORT.md` beside the build sheet, a separate
file so the build-sheet validator is unaffected: workspace ID and environment,
run ID and time, role map, delivery setting, pre-flight result, then one table
`| Case | Profile | Setup | Expected | Observed | Seconds | Result |` with
Result one of PASS, FAIL, WARN, CAN'T CHECK, STRUCT rows first. Verdict: PASS
(all PASS), PASS WITH WARNINGS (only WARN or CAN'T CHECK besides PASS, each
with its reason), or FAIL. A FAIL goes back to the BUILD stage that made the
object (stages 4-5 for segments, 8 for automations), is fixed there in place,
and gets a fresh smoke run. Say plainly in the reply that nothing was started,
sent or deleted, and which profiles were created and parked.

## Next
Inside BUILD, continue with stage 9 of `protocols/build.md`: the build sheet,
the rollback list (with the parked `smk-` profiles under "Smoke profiles:
remove in the app") and the activation checklist, whose first line is "Smoke
report: PASS" or each WARN accepted by name. On its own, report the S8 verdict
and run `protocols/self-refine.md` at session end.

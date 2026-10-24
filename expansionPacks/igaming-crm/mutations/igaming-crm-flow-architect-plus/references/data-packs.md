# Data packs handshake

Context: LIVE-AUDIT has two sections. "Configuration audit" (P findings)
compares the workspace objects with the libraries and needs only this skill.
"Data exploration" (X findings) reads what the profile and delivery data
show, and runs the AUDIT packs of a workspace-specific data-analyst skill
when one is installed. BUILD stage 0b reads the gate-readiness pack's table
when its output is supplied. This file is the whole contract between the two
skills; nothing else in this skill depends on the data skill's internals.

## Contents
- What counts as installed
- Packs consumed
- Output contract
- Pack rows to X findings
- Gate-readiness pack to BUILD stage 0b
- Without the data skill

## What counts as installed
A workspace-specific data-analyst skill: one per operator, named for example
`<operator>-crm-data-analyst`, exposing validate_pack_output.py in its scripts folder and
the seven AUDIT packs listed below. It is installed for this run only when all
of these hold:
1. The skill list of the session shows it, and its folder holds
   validate_pack_output.py under scripts and the seven pack files.
2. Its description or its workspace table names the workspace ID chosen at
   intake (hard rule 2). A data skill written for another workspace is not
   installed for this one.
3. The user confirms, in this run, that it is the data skill for this
   workspace. Never pick one by a name match alone.
This skill never names the operator; quote the data skill by its folder name
only in the run's reply, never in a deliverable.

## Packs consumed
| Pack | Answers | Feeds |
|---|---|---|
| audit-data-completeness | coverage of key attributes, completeness score, cross-field contradictions | X findings on data quality; BUILD stage 1 report |
| audit-gate-readiness | which of the fourteen gate attributes exist and hold real values; the suppression segment against the canon | X findings on the gate; BUILD stage 0b row for stage 1 |
| audit-segment-integrity | segments against their stated logic, recounts | X findings on segment reliability |
| audit-automation-health | states, failing steps, disabled channels, orphan actions, stale tests | X findings on delivery and routing (configuration gaps stay P findings) |
| audit-deliverability | delivered, suppressed and bounced per send, with reasons | X findings on list quality and reach |
| audit-consent | consent and unsubscribe completeness and consistency | X findings on consent quality |
| audit-audience-pollution | staff, test, underage and geo-mismatch profiles in the marketing base | the company, staff and test account step (`protocols/live-audit.md` step 4) and its X findings |
The data skill's validation, management and tactical packs are not part of
LIVE-AUDIT; offer them to the user as a follow-up.

## Output contract
- Run each pack by the data skill's own procedure. Its hard rules apply in
  full, including its per-call approval for POST reads; this skill adds no
  call of its own and never writes.
- Before a pack output is used, run
  `python3 <data-skill>/scripts/validate_pack_output.py PACK-OUTPUT.md` and
  require exit 0. Exit 1: let the data skill fix the output; a pack that
  still fails is listed under "Not evidenced" with the validator's codes.
- The output must name the same workspace ID as this run and carry its
  labels: Workspace, As of (UTC), Window, Exclusions applied, Basis.
- Copy each number with its basis (`exact` or `sampled`), its as-of time and
  the pack name. Never recompute a pack's number by hand, and never put a
  pack's number into a P finding without saying it came from the pack.
- Aggregates only: no email, name, phone or IP in a finding. Profile IDs only
  in a worklist the user asked for, through the data skill.

## Pack rows to X findings
- One X finding per pack row that breaks a rule of the libraries (the pack
  lists the rules it validates on its last line). Several rows with one fix
  are one finding.
- Risk: the pack's own label when it gives one (the packs use the same
  rubric); otherwise the rubric in `protocols/design-audit.md` step 4.
- Owner: data model, identify sync, attribute types and source-side data
  quality go to the Backend Engineer; consent policy, RG policy, offer content
  and exposure records to the Compliance & RG Officer; segments, automations,
  broadcasts, caps and deliverability settings to the CRM Manager;
  multi-accounting, bonus abuse, KYC-before-withdrawal and AML signals to the
  Fraud & AML Analyst.
- Objects: the segment, automation or broadcast the pack row names, as deep
  links (`protocols/live-audit.md`, "Ledger reference"); the pack output
  file goes under "Data" in the finding.
- Verify: the pack's read, quoted as the GET call and the value it must show
  after the fix.
- A pack finding that changes a P finding (confirms, weakens or corrects it)
  goes into "Effect on the configuration audit" in the ledger, naming both
  labels.

## Gate-readiness pack to BUILD stage 0b
When the user supplies an audit-gate-readiness output that passes the output
contract, has an as-of time within 24 hours and names the build's workspace,
stage 0b takes its table instead of re-deriving the stage 1 row:
| Pack column | Pre-flight use |
|---|---|
| Gate attribute, operator field, In data index | stage 1 NO-GO when any gate attribute is not in the data index, or is present only under an operator field the user has not confirmed as the mapping |
| Set, Missing (leak if negated) | Observed cell; a Missing count above 0 is written in the Fix cell as the leak size and becomes the G10 expectation in `protocols/smoke.md` |
| True / blocking value, Enum valid | Observed cell; an invalid enum is reported with its proposed transform (`references/data-model.md`, "Mapping operator field names") |
| Verdict line ("BUILD stage 1 would stop: ..." or "ready") | the `Pre-flight: stage 1 GO\|NO-GO: <reason>` line, with "(audit-gate-readiness, as of <time>)" at the end |
| Suppression segment leaves against the canon | a note on the stage 4 row; it does not change the stage 4 verdict |
Older than 24 hours, another workspace, or a failed validator: say so and
re-derive the row with the reads in `references/build-order.md`. Every other
stage row of the pre-flight is always read live.

## Without the data skill
Configuration audit runs in full. The Data exploration section holds one line
instead of findings: "Data exploration skipped: <reason>", where the reason
is one of: no workspace-specific data-analyst skill is installed; the
installed one is for another workspace; the user did not confirm it; the user
declined its POST-read approvals; every pack output failed its validator. The
summary band repeats the reason under "Not evidenced". The company, staff and
test account step of `protocols/live-audit.md` still runs, from the reads this
skill makes itself (`GET .../customers` filter counts on the markers the user
named). Stage 0b re-derives its stage 1 row as before.

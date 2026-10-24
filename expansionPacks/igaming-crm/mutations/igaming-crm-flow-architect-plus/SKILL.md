---
name: "igaming-crm-flow-architect-plus"
description: "Builds, smoke-tests and audits iGaming CRM in a Customer.io workspace through the official Customer.io MCP. Turns a casino or sportsbook CRM design (suppression gate, segments, topics, frequency caps, webhooks, journeys) into workspace objects in a safe, idempotent order, leaves every automation in draft with responsible-gambling exits, writes a build sheet and rollback list, proves the gate with parked synthetic profiles, and audits a live workspace read-only. Can produce the design first. Use when the user asks to build, implement, deploy, push or create a CRM blueprint, segment set, suppression gate or journey in Customer.io, to turn a blueprint into automations, to smoke-test or verify a build or a live gate, or to audit a gambling operator's live Customer.io workspace. Do not use for pure design requests with no workspace involved (igaming-crm-flow-architect), Customer.io troubleshooting such as a failing webhook or delivery, or drafting email copy or templates."
license: MIT
compatibility: Requires the official Customer.io MCP server (cio_* tools) for BUILD and LIVE-AUDIT; design modes work without it.
disable-model-invocation: true
mutation: true
source_url: "claude.ai account skill igaming-crm-flow-architect-plus v1.2.0 (no public URL)"
original_skill: original/UPSTREAM.md
metadata:
  version: "1.2.0"
  author: admariner
  pack: igaming-crm
  lifecycle: beta
---

# iGaming CRM Flow Architect Plus

Designs player-lifecycle CRM for casino and sportsbook operators and builds it in
Customer.io. The design layer is the v1.1 skill, copied in; the build layer adds a
fixed, dependency-ordered build through the official Customer.io MCP. Customer.io's
own skills own the platform mechanics; this skill owns the iGaming policy and the
order. Tools are named bare (`cio_read_api`) because the server prefix differs by
region and install (for example `mcp-eu_customer_io:cio_read_api`).

## Hard rules (every mode, in this order)
1. Never activate, start, restart or schedule an automation; never send anything
   (no test sends, no events, no broadcast triggers, no `sending_state:
   "automatic"`); never delete people or objects (`cio_delete_api` is never
   called); never call `suppress`, which deletes the profile and its audit
   trail. Activation and every deletion belong to the user. The one exception
   to "no writes to people" is rule 9.
2. Choose the workspace explicitly every run: list the allowed workspaces from
   `cio_auth_status`, ask which one, never assume or reuse an earlier answer.
   Detail: `references/workspace-safety.md`.
3. Preview every write with `dry_run` and show the previews to the user, grouped
   per build stage, before executing that stage. No approval, no write.
4. Read the Customer.io skill (`cio_skills_read`) for each resource type before
   touching it; the API has silent failures a schema does not show. Map:
   `references/build-order.md`.
5. Find by name before create. Object names carry the spec ID
   (`references/object-naming.md`), so a re-run finds and reuses what exists
   instead of duplicating it.
6. Every marketing automation (MKT_, VIP_) gets the RG exit conditions
   (`templates/rg-exit-block.md`), a subscription topic and a frequency-cap
   opt-in, or it is not created.
7. End every BUILD with the build sheet, the rollback list
   (`templates/build-sheet.md`, `templates/rollback-list.md`) and the smoke
   report (or the user's recorded reason for skipping it), and run
   `scripts/validate_build_sheet.py` on the planned sheet before the first
   write and on the final sheet until it exits 0.
8. The v1.1 design rules hold for every design artifact: real conditions and
   values, no placeholders; the suppression gate, `RG_EXIT_BLOCK` and the L4
   pre-send check on every marketing send; never name a client or source
   operator; market facts only from `references/markets.json`, with a
   `closed_pending` market's banner on line 1; end with the legal notice in
   `protocols/self-check.md`.
9. Smoke profiles are the only people this skill may write. SMOKE
   (`protocols/smoke.md`) may create and update profiles whose ID starts with
   `smk-`, with no email, phone or device, after a dry run and the user's
   approval, and never touches any other profile. For those profiles only,
   this rule overrides the "People" line of the never list in
   `references/workspace-safety.md` and adds `POST .../customers` and
   `PUT .../customers/{customer_id}` to its allowed calls; every other line of
   that file still holds.

## Modes
| Mode | Asked for | Protocols | Output |
|---|---|---|---|
| DESIGN | A blueprint, one journey, segment set, gate, RG automation or cap set, or a review of a shared export | `protocols/blueprint.md`, `protocols/flow.md`, `protocols/design-audit.md` | The v1.1 deliverables |
| BUILD | Create the design's objects in a Customer.io workspace | `protocols/build.md`, then `protocols/smoke.md` as stage 8b | Workspace objects in draft, build sheet, rollback list, smoke report, activation checklist |
| SMOKE | Prove the gate and the draft journeys sort test players correctly, after a BUILD or on any workspace | `protocols/smoke.md` | Smoke report; parked `smk-` profiles; nothing started or sent |
| LIVE-AUDIT | Review the live workspace against the libraries and explore its data | `protocols/live-audit.md` | Two-section findings ledger (Configuration audit P, Data exploration X) with owners, fixes and verify checks; markdown, plus an HTML ledger where artifacts exist; nothing written |

BUILD needs a design first. When the user has none, run DESIGN (FLOW or
BLUEPRINT) for the requested scope, then BUILD from it.

BUILD runs the smoke test as stage 8b, after the automations read back in
draft and before the build sheet. In a sandbox it runs by default; in
production it is offered and runs only on the confirmation in S1. The
activation checklist (build stage 10) gains a first line: "Smoke report:
PASS", or each WARN accepted by name. Start nothing on FAIL. After a
LIVE-AUDIT, offer SMOKE for the workspace's suppression gate.

LIVE-AUDIT, and any analysis of profile or delivery data: before reading a
pattern as player behaviour, list abuse or fraud, ask the user how company,
staff and test accounts are marked, report them as a separate group, and file
every such account without the staff flag as its own hygiene finding. Detail:
`protocols/live-audit.md` step 4. Data exploration uses a workspace-specific
data-analyst skill when one is installed, and says why when it is skipped
(`references/data-packs.md`).

## Smoke test
SMOKE proves, with a few parked synthetic `smk-<run>-` profiles, that the gate
segments put each kind of player on the right side and that each draft
marketing automation would admit the eligible player and refuse the
suppressed one, without starting, sending or deleting anything. It does not
replace the manual QA matrix in `references/qa-launch.md`. Steps S1-S8
(workspace and identifier check, role map, structural checks, gate cases
G1-G11 and journey pairs, collision pre-flight, create, observe, park, report
in `SMOKE-REPORT.md` beside the build sheet): `protocols/smoke.md`.

## Workflow
1. Intake: `protocols/intake-plus.md` (at most five questions; workspace,
   environment and build-or-design are merged in), then `protocols/intake.md`
   steps 3-8 for the design inputs.
2. Run the mode protocol. Load only the references it lists for the step in hand.
3. Check before delivery: design artifacts through `protocols/self-check.md`;
   BUILD through `scripts/validate_build_sheet.py` and the smoke verdict;
   SMOKE through its S8 verdict; LIVE-AUDIT through `protocols/self-check.md`
   with `--mode audit`.
4. At session end: `protocols/self-refine.md`.

## Map
Protocols:
- `protocols/intake-plus.md` merged questions, mode choice, workspace choice.
- `protocols/intake.md` design inputs: licence posture, markets, events, platform.
- `protocols/blueprint.md` DESIGN, 17-section blueprint.
- `protocols/flow.md` DESIGN, one piece.
- `protocols/design-audit.md` DESIGN, review of a shared export; risk rubric.
- `protocols/build.md` BUILD, stages 0-10 (stage 0 includes the readiness
  pre-flight; stage 8b is `protocols/smoke.md`).
- `protocols/smoke.md` SMOKE, S1-S8, cases, pre-flight, report.
- `protocols/live-audit.md` LIVE-AUDIT, read-only pull, data exploration, ledger.
- `protocols/self-check.md` validator, judgement pass, notice.
- `protocols/self-refine.md` end-of-session improvement.

References (build layer):
- `references/build-order.md` stage order, cio skills per stage, confirmed endpoints.
- `references/object-naming.md` spec ID in every object name; find-by-name rules.
- `references/workspace-safety.md` dry-run, approvals by verb, never list, sandbox vs production.
- `references/rollback.md` what the user can remove, what never, and in which order.
- `references/data-packs.md` handshake with a workspace-specific data-analyst
  skill: packs, output contract, gate-readiness table for stage 0b.

References (design layer, from v1.1):
- `references/data-model.md`, `references/event-taxonomy.md` attributes, enums, events.
- `references/segment-library.md` every SEG_* with exact logic.
- `references/suppression-gate.md` gate, L1-L4, the calls hard rule 1 forbids.
- `references/responsible-gambling.md` RG signals, level actions, VIP rules.
- `references/subscription-topics.md` six topics and unsubscribe mechanics.
- `references/journey-catalogue.md` 15 journeys, 16 dimensions, timing rule.
- `references/journey-flows-onboarding.md`, `references/journey-flows-engagement.md`,
  `references/journey-flows-protective.md` the journey flows.
- `references/caps-and-priority.md` cap table, frequency caps, priority.
- `references/liquid-patterns.md` personalisation, snippets.
- `references/compliance-and-overlays.md`, `references/markets.json` market overlays.
- `references/kpis-and-testing.md` KPIs, A/B rules, content rubric.
- `references/platform-implementation.md` Customer.io facts, mapping table.
- `references/qa-launch.md` QA matrix, launch sequence, kill switch.
- `references/legal-question-bank.md` questions for counsel.

Templates: `templates/blueprint-outline.md`, `templates/journey-spec.md`,
`templates/flow-table.md`, `templates/audit-findings.md`,
`templates/rg-exit-block.md`, `templates/build-sheet.md`,
`templates/rollback-list.md`, `templates/live-audit-findings.md` (ledger,
canonical), `templates/live-audit-ledger.html` (its HTML rendering).

Scripts (run, do not read; Python 3.8+, standard library only):
- `scripts/validate_crm_output.py` checks design deliverables (`--help`).
- `scripts/validate_build_sheet.py` checks a build sheet; exit 0 pass, 1 fail, 2 usage.
- Fixtures in `scripts/fixtures/`: `good.md`, `bad.md`, `good-markets.md`,
  `bad-markets.md`, `markets-stale.json`, `good-build-sheet.md`,
  `good-created-build-sheet.md` (with its `SMOKE-REPORT.md`),
  `stopped-build-sheet.md`, `empty-build-sheet.md`, `bad-build-sheet.md`,
  `good-live-audit.md`, `bad-live-audit.md`;
  commands in
  `protocols/self-refine.md` step 5.

Changes are logged in `CHANGELOG.md`.

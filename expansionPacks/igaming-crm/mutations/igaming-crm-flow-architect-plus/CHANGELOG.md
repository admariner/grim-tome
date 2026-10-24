# Changelog

Changes to this skill, newest first. One entry per change: date, what changed, files.

## 1.2.0 (2026-10-24)
- LIVE-AUDIT accounts for company, staff and test profiles: ask how they are marked, count them apart, one hygiene finding per marker (SKILL.md, protocols/live-audit.md).
- SMOKE: attribute conditions read back as `attribute_change` are current-value checks, not change history (protocols/smoke.md).
- LIVE-AUDIT has two sections, Configuration audit and Data exploration. Data exploration runs the AUDIT packs of a workspace-specific data-analyst skill when one is installed and confirmed, and records why it was skipped otherwise; build stage 0b can take the gate-readiness table from it (references/data-packs.md, protocols/build.md, references/build-order.md).
- The live-audit findings template is the canonical ledger (summary by risk, P and X findings with owner, fix, docs, verify), with an HTML rendering (templates/live-audit-findings.md, templates/live-audit-ledger.html).
- Validator check C30 for the ledger, with fixtures good-live-audit.md and bad-live-audit.md (scripts/validate_crm_output.py).

## 1.1.0 (2026-10-24)
- Stage 0b readiness pre-flight: GET reads only, one GO/NO-GO row per later stage (gate attributes, subscription center and topics, snippets, segment allowance, frequency cap channels, webhook access), written as "Pre-flight:" lines in the planned sheet, so blockers surface in one run instead of one stage per run (protocols/build.md, references/build-order.md).
- Build-order notes: a subscription center that is off with no topics, a segment allotment of 0 and webhook reads refused on a non-admin token all block their stage.
- SMOKE mode and hard rule 9: parked `smk-` synthetic profiles prove the gate; S1-S8 live in protocols/smoke.md; build stage 8b; smoke profiles on the rollback list; "Smoke report: PASS" first on the activation checklist.
- Build sheet validator checks B15 (Pre-flight line shape) and B16 (smoke report beside the sheet), both warnings (scripts/validate_build_sheet.py).

## 1.0.0 (2026-10-20)
- Created from the design-only skill v1.1.0: BUILD and LIVE-AUDIT modes, the hard rules (never activate, send or delete; explicit workspace; dry run and approval per stage; read the Customer.io skill per resource; find by name before create; RG exits, topic and frequency cap on every marketing automation; build sheet and rollback list), build-sheet validator and fixtures. Audit renamed design-audit; caps re-based on named frequency caps.
- After a fresh-context test: a correctly stopped build passes its validator (B01 warning on "Stopped at stage N:"); per-message topics checked (B08/B09); RG_EXIT_BLOCK is one `{"or": [...]}` exit element; stage 1 proposes the field mapping; rollback coverage check B14; planned sheet validated before the first write.

## Design layer (v1.1.0, carried into 1.0.0)
- Market facts moved to references/markets.json with status and verified date; BR flows carry a closed-pending banner (C28 warning).
- RG_EXIT_BLOCK template on every MKT and VIP journey.
- Event-triggered journeys read the event payload first, because attributes sync minutes behind the event (RG_12, VIP_11, MKT_03).
- TXN_01 verification reminders exclude self-excluded, register-matched and timed-out players; MKT_03 entry and MKT_08/MKT_09 cap timing fixed.
- Validator resolves full market names to codes.

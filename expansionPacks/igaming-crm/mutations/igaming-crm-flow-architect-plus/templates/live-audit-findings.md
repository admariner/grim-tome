Live audit · Customer.io [[REGION]] · workspace [[WORKSPACE_ID]] · [[sandbox|production]] · [[YYYY-MM-DD]]

# Workspace [[WORKSPACE_ID]] audit

[[LEDE: one or two sentences. A read-only review of the live CRM configuration and data against the iGaming player-protection rules; every finding has an owner, a fix and read-only verify checks.]]

Facts: [[N]] automations ([[N]] running) · [[N]] sent broadcasts · [[N]] segments · [[N]] frequency caps · [[N]] topics · [[N]] webhooks · [[N]] profiles · Nothing was written to the workspace.

## Summary

| Risk | Configuration audit | Data exploration | Total |
|---|---|---|---|
| player-protection | [[N]] | [[N]] | [[N]] |
| compliance | [[N]] | [[N]] | [[N]] |
| revenue | [[N]] | [[N]] | [[N]] |
| hygiene | [[N]] | [[N]] | [[N]] |
| All findings | [[N]] | [[N]] | [[N]] |

Not evidenced: [[CALLS_THAT_FAILED, POST_ONLY_READS, PACKS_NOT_RUN, OUT_OF_SCOPE_ITEMS]]
Data exploration: [[N packs from the workspace data-analyst skill, as of YYYY-MM-DDTHH:MMZ | skipped: REASON from references/data-packs.md]]
Company, staff and test accounts: [[MARKERS_THE_USER_NAMED]]; [[N]] accounts counted as a separate group and kept out of player figures.

## Configuration audit: [[N]] findings

| Priority | Area | Object | Finding | Risk | Owner | Fix |
|---|---|---|---|---|---|---|
| P1 | [[AREA]] | [[OBJECT_NAME]] ([[ID]]) | [[FINDING_WITH_LIVE_CONDITION_QUOTED]] | [[RISK_ENUM]] | [[OWNER_ROLE]] | [[EXACT_FIX]] |

## Data exploration: [[N]] findings

| Priority | Area | Object | Finding | Risk | Owner | Fix |
|---|---|---|---|---|---|---|
| X1 | [[AREA]] | [[OBJECT_OR_DASH]] | [[FINDING_WITH_COUNT_AND_BASIS]] | [[RISK_ENUM]] | [[OWNER_ROLE]] | [[EXACT_FIX]] |

Effect on the configuration audit:
- [[P_LABEL]]: [[HOW_AN_X_FINDING_CONFIRMS_WEAKENS_OR_CORRECTS_IT]]

Risk is one of `player-protection`, `compliance`, `revenue`, `hygiene`; each
table is sorted in that order, then by effort. Use these exact columns; the
validator checks them with `--mode audit`.

## Findings

### P1 · [[TITLE]]
- Risk: [[RISK_ENUM]]
- Owner: [[OWNER_ROLE]]
- Area: [[AREA]]
- Objects: [Automation [[ID]]]([[HOST]]/workspaces/[[WORKSPACE_ID]]/journeys/automations/[[ID]]/overview)
- Finding: [[WHAT_THE_LIVE_OBJECT_DOES, CONDITION_QUOTED]]
- Fix: [[EXACT_CONDITION_OR_SETTING]]
- Docs: [[[DOC_LABEL]]]([[DOCS_CUSTOMER_IO_URL]])
- Data: [[PACK_OUTPUT_FILE, X findings only; omit the line otherwise]]
- For the owner:
  1. [[STEP_IN_THE_APP_OR_BACKEND]]
- Done when:
  - [ ] [[CHECKABLE_OUTCOME]]
- Agent task: [[null | the block below]]
  ```text
  [[AGENT_TASK_PREAMBLE]]
  Task P1: [[TITLE]]
  1. Read [[CIO_SKILL_PATHS]] with cio_skills_read.
  2. GET [[OBJECT]] in full.
  3. Prepare [[CHANGE]] and send it with dry_run true.
  4. Show me the preview and wait for my approval. Do not change the automation state.
  ```
- Verify:
  1. `GET [[PATH]]`: [[FIELD]] must [[EXPECTED_VALUE]].

### X1 · [[TITLE]]
[[same fields as P1]]

## Market overlay: [[MARKET_CODE]] ([[MARKET_NAME]])
One block per intake market, from its `references/markets.json` row, so
`--markets` passes on the first run; add `(verify before deployment)` to the
block and its helpline line when the row is not primary.
- Live finding: [[WHAT_THE_WORKSPACE_DOES_FOR_THIS_MARKET]]
- Suppression and register: [[REGISTER_AND_HOW_THE_MATCH_REACHES_THE_PROFILE]]
- Disclosures: helpline [[HELPLINE]]; licence footer; 18+.
- RG requirements: [[RG_REQUIREMENT]]
- Bonus rules: [[BONUS_RULES_FROM_THE_ROW]]

Agent prompts assume a Claude session connected to the Customer.io MCP ([[REGION]]). Every task prompt asks for a dry run and your approval before any write, and none of them starts, stops, sends or deletes anything. Fixes can be applied in a separate BUILD run after you approve them.

Legal/compliance review required: have qualified legal and compliance counsel review this design in every target jurisdiction before deployment.

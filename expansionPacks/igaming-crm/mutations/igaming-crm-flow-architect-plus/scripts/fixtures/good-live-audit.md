Live audit · Customer.io US · workspace 100001 · sandbox · 2026-10-24

# Workspace 100001 audit

Facts: 4 automations (1 running) · 2 sent broadcasts · 9 segments · 1 frequency cap · 0 topics · 0 webhooks · 120 profiles · Nothing was written to the workspace.

## Summary

| Risk | Configuration audit | Data exploration | Total |
|---|---|---|---|
| player-protection | 1 | 0 | 1 |
| compliance | 1 | 0 | 1 |
| revenue | 0 | 0 | 0 |
| hygiene | 0 | 1 | 1 |
| All findings | 2 | 1 | 3 |

Not evidenced: reporting webhooks (the read returned 403); data packs other than audience-pollution.
Data exploration: 1 pack from the workspace data-analyst skill, read at 2026-10-24T09:00Z.
Company, staff and test accounts: staff flag and the operator's own email domain; 14 accounts counted as a separate group and kept out of player figures.

## Configuration audit: 2 findings

| Priority | Area | Object | Finding | Risk | Owner | Fix |
|---|---|---|---|---|---|---|
| P1 | Exit conditions | Second deposit automation (13) | Exit conditions are only "in segment 25"; no attribute exits | player-protection | CRM Manager | Add the RG_EXIT_BLOCK attribute exits as one OR group |
| P2 | Frequency | Default cap | The only cap is email 3 per 7 days, used by one broadcast | compliance | CRM Manager | Create LIM_EMAIL_MKT_STD with email 1 per 86400 s and 4 per 604800 s |

## Data exploration: 1 finding

| Priority | Area | Object | Finding | Risk | Owner | Fix |
|---|---|---|---|---|---|---|
| X1 | Internal accounts | - | 11 accounts on the operator's own email domain carry no staff flag (exact) | hygiene | Backend Engineer | Send is_staff true for every own-domain account in the identify sync |

## Findings

### P1 · Running automation 13 exits only on segment 25
- Risk: player-protection
- Owner: CRM Manager
- Area: Exit conditions
- Objects: [Automation 13](https://fly.customer.io/workspaces/100001/journeys/automations/13/overview), [Segment 25](https://fly.customer.io/workspaces/100001/journeys/segments/25)
- Finding: Exit conditions are only "in segment 25"; leaving depends on segment recomputation.
- Fix: Add the RG_EXIT_BLOCK attribute exits as one OR group.
- Docs: [Exit conditions](https://docs.customer.io/journeys/send/campaigns/exit-conditions/)
- For the owner:
  1. Open automation 13 and go to its exit settings.
  2. Add the RG exit conditions as one OR group and save.
- Done when:
  - [ ] Exit conditions saved
  - [ ] Automation state unchanged
- Agent task:
  ```text
  Workspace 100001 (Customer.io US, sandbox). Call cio_auth_status first and confirm 100001 is allowed.
  Task P1: Running automation 13 exits only on segment 25
  1. Read fly-api/automations.md with cio_skills_read.
  2. GET automation 13 in full.
  3. Prepare the exit conditions update and send it with dry_run true.
  4. Show me the preview and wait for my approval. Do not change the automation state.
  ```
- Verify:
  1. `GET /v1/environments/100001/campaigns/13`: the exit conditions must include the RG_EXIT_BLOCK attributes and segment 25.
  2. The state must be unchanged.

### P2 · Only one cap exists and it has no daily rule
- Risk: compliance
- Owner: CRM Manager
- Area: Frequency
- Objects: [Message frequency limits](https://fly.customer.io/workspaces/100001/settings/actions/message_frequency_limits)
- Finding: The only cap is the legacy default, email 3 per 7 days.
- Fix: Create LIM_EMAIL_MKT_STD with email 1 per 86400 s and 4 per 604800 s.
- Docs: [Set up frequency limits](https://docs.customer.io/messaging/send/message-limits/set-up-message-limits/)
- For the owner:
  1. Open Message frequency limits and create LIM_EMAIL_MKT_STD with both rules.
- Done when:
  - [ ] LIM_EMAIL_MKT_STD saved with two rules
- Agent task: Read fly-api/frequency_caps.md, GET /frequency_caps, prepare the create with dry_run true, show me the preview and wait for my approval.
- Verify:
  1. `GET /v1/environments/100001/frequency_caps`: LIM_EMAIL_MKT_STD must hold an email 1-per-86400 rule and an email 4-per-604800 rule.

### X1 · Own-domain accounts carry no staff flag
- Risk: hygiene
- Owner: Backend Engineer
- Area: Internal accounts
- Objects: none
- Finding: 11 accounts on the operator's own email domain carry no staff flag (audience-pollution pack, exact).
- Fix: Send is_staff true for every own-domain account in the identify sync.
- Docs: [Track API (identify)](https://docs.customer.io/api/track)
- Data: audience-pollution pack output
- For the owner:
  1. Set is_staff true for every own-domain account and send it in the identify sync.
- Done when:
  - [ ] Own-domain accounts flagged
- Agent task: null
- Verify:
  1. `GET /v1/environments/100001/customers` filtered on is_staff: the own-domain accounts must all read true.

Agent prompts assume a Claude session connected to the Customer.io MCP (US). Every task prompt asks for a dry run and your approval before any write, and none of them starts, stops, sends or deletes anything. Fixes can be applied in a separate BUILD run after you approve them.

Legal/compliance review required: have qualified legal and compliance counsel review this design in every target jurisdiction before deployment.

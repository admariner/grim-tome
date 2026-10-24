# Protocol: live-audit

Context: runs after intake-plus chose LIVE-AUDIT. It pulls the live
configuration of the chosen Customer.io workspace read-only, compares it with
the libraries, explores the profile and delivery data, and ranks the gaps by
player-protection risk. It never writes.

## Contents
- Mission
- Steps 1-7 (pull, data exploration, map, company and staff accounts,
  compare, ledger, self-check)
- Guidelines
- Ledger reference (labels, risks, owners, link patterns, docs,
  agent and verify preambles)
- Next

## Mission
A two-section findings ledger: "Configuration audit" (P findings: every
automation, broadcast, segment, frequency cap, topic and webhook in scope
against the libraries) and "Data exploration" (X findings: what the profile
and delivery data show). Each finding carries one risk value, one owner,
deep links, an exact fix, owner steps, an agent task or none, and read-only
verify checks, built from `cio_read_api` calls only.

## Steps
1. Confirm the workspace ID and environment from intake-plus, call
   `cio_auth_status` and `cio_prime`, and read fly-api/automation_review.md,
   fly-api/segment_conditions.md and fly-api/frequency_caps.md with
   `cio_skills_read`. Use `cio_read_api` only; `cio_write_api` and
   `cio_delete_api` are not called in this mode, and a POST-only read is
   skipped and recorded as "not evidenced". Note the region from
   `cio_auth_status` (it sets the link host in step 6). Done when the
   workspace is confirmed and the three skills are read.
2. Pull, reading full objects where a field's absence would become a finding
   (a field is missing only when the API returns it empty, never because a
   `jq` filter left it out):
   - Automations: `GET .../campaigns`, every page (20 per page, `page` 0-based,
     until a page holds fewer than 20); then `GET .../campaigns/{campaign_id}`
     for each, plus `GET .../campaigns/{campaign_id}/validate`.
   - Broadcasts: `GET .../newsletters`, then each sent, draft or scheduled
     one in full (audience filters, `send_to_everyone`, topic, cap mode).
   - Segments: `GET .../segments` with `size`, every page; then
     `GET .../segments/{segment_id}` for every segment an automation or
     broadcast uses and every name matching the segment library.
   - Frequency caps: `GET .../frequency_caps`, `GET .../frequency_caps/{frequency_cap_id}/usage`,
     and `GET .../message_limits` (legacy; it lists automations with limits on).
   - Topics: `GET .../subscription_topics` and
     `GET .../subscription_topic_messages/list`.
   - Webhooks: `GET .../webhooks` and `GET .../webhook_configurations_minimal`
     (never the full configuration list, which returns secrets).
   - Data model: `GET .../attributes` and `GET .../event_names`.
   Done when every list is pulled or its call is recorded as failed, and the
   facts strip counts (automations and running, broadcasts sent, segments,
   caps, topics, webhooks, profiles) are known.
2b. Data exploration, with the handshake in `references/data-packs.md`:
   check whether a workspace-specific data-analyst skill is installed for this
   workspace and confirmed by the user; if so, run its seven AUDIT packs
   (data-completeness, gate-readiness, segment-integrity, automation-health,
   deliverability, consent, audience-pollution) by its own procedure, check
   each output with its `validate_pack_output.py`, and keep the outputs as the
   Data links of the X findings. If not, record "Data exploration skipped:
   <reason>" for the ledger. Done when every pack output passed its validator
   or is listed as not evidenced, or the skip reason is recorded.
3. Map each object to the libraries by name (`references/object-naming.md`);
   objects without a spec ID are matched by purpose and listed as "unnamed".
   Inventory them into the five lists of `protocols/design-audit.md` step 2.
   Done when every pulled automation, broadcast and segment appears in the
   inventory.
4. Company, staff and test accounts, before any profile or delivery pattern
   is read as player behaviour, list abuse or fraud: ask the user how company,
   staff and test accounts are marked (staff flag, role, the operator's own
   email domain, company referrer or affiliate IDs). Count them as a separate
   group (the audience-pollution pack when installed, otherwise
   `GET .../customers` filter counts on each marker), state the group in every
   X finding whose numbers it touches, and keep it out of player figures.
   File every such account without the staff flag as its own hygiene finding
   (one X finding per marker, with the count, owner Backend Engineer), never
   folded into a player-behaviour finding. Done when the markers are
   recorded, the group is counted, and each unflagged marker has its finding.
5. Compare in the order of `protocols/design-audit.md` step 3, adding these
   live checks, each a P finding when it fails:
   - Every running or draft marketing automation has `RG_EXIT_BLOCK` in its
     exit conditions, its gate entry, a subscription topic and a frequency
     limit (`use_message_limits` with a cap); `send_to_unsubscribed` is false.
   - Every sent, draft or scheduled marketing broadcast has
     `send_to_everyone` false, an audience that requires the gate segment, a
     topic and a cap.
   - `SEG_CAN_RECEIVE_MARKETING` (or the operator's gate) carries all fourteen
     gate conditions and none of them reads an attribute missing from the
     workspace's data index. An attribute condition reads back as
     `type: "attribute_change"`; it is a current-value check, never report it
     as change history.
   - No automation sends RG or service mail under a marketing topic or a cap.
   - Every Wait Until has a timeout (`exit_type: "continue"`, `delay` > 0);
     every reactivation journey's trigger is a segment or attribute, not
     several events.
   - Message actions marked automatic in a draft or stopped marketing
     automation that lacks the gate (it would send on start).
   - A reporting webhook feeding the counter service exists and is enabled.
   Done when every inventory item has been compared.
6. Ledger: fill `templates/live-audit-findings.md`.
   - Label and sort with the risk rubric of `protocols/design-audit.md` step 4
     (player-protection, compliance, revenue, hygiene; inside a band, lowest
     effort first). Configuration findings are P1..Pn, data findings X1..Xn,
     each section sorted on its own.
   - Give each finding one owner: Compliance & RG Officer (policy, consent,
     offer content, exposure records, counsel), CRM Manager (Customer.io
     objects), Backend Engineer (attributes, identify sync, endpoints,
     source data), Fraud & AML Analyst (multi-accounting, bonus abuse, KYC
     and withdrawals, AML).
   - Per finding: area, title, Objects as deep links by ID (link patterns
     in "Ledger reference" below), Finding quoting the live condition, Fix,
     Docs (official docs.customer.io pages), For the owner (numbered steps) with a Done-when
     checklist, Agent task, and Verify (exact GET reads and what each must
     show). The Agent task always says: read the named Customer.io skill, GET
     the object in full first, send every write with `dry_run`, show the
     preview, wait for approval, never change automation state. Write `null`
     when the fix is not an API task (a backend change, a compliance
     decision, or a start, stop, archive, send or delete, which belong to the
     user).
   - Header (eyebrow, title, lede, facts strip ending "Nothing was written to
     the workspace"), summary band (findings by risk with counts, Not
     evidenced), one Market overlay block per intake market from its
     `references/markets.json` row, footer.
   - Markdown is the canonical deliverable: header, summary, the two section
     tables, then the per-finding blocks in that order. When the host offers
     artifacts, also render the same content into
     `templates/live-audit-ledger.html` (risk and owner filters, copy buttons
     for the owner instructions, checklist, agent task and verify prompt) and
     publish it; it never holds more than the markdown.
   Done when every finding has a label, one risk, one owner, a Fix and at
   least one Verify check, and both sections have a count.
7. Run `protocols/self-check.md` with `--mode audit` on the markdown ledger.
   Exit 1: fix the ledger and re-run. Done when it exits 0.

## Guidelines
- Pattern: one finding per defect; a missing exit on three automations is
  three findings, because each is fixed separately. Several objects with one
  identical fix may share one finding that lists every object.
- Pattern: offer BUILD for the fixes as a follow-up, never inside this run.
- Anti-pattern: reporting an absent field from a filtered read; re-read the full
  object first.
- Anti-pattern: naming the workspace's brand or operator in the deliverable;
  use "the operator" and the workspace ID.

## Ledger reference
Rules for filling `templates/live-audit-findings.md` (and the HTML ledger,
which takes the same values):
- Markdown is the canonical deliverable, in this order: header, summary,
  Configuration audit table, Data exploration table, per-finding blocks,
  market overlays, footer. The HTML ledger (`templates/live-audit-ledger.html`)
  renders the same content and never holds more.
- Labels: P1..Pn for Configuration audit, X1..Xn for Data exploration; each
  table sorted player-protection, compliance, revenue, hygiene, then lowest
  effort first. The Priority cell holds the label.
- Risk: player-protection | compliance | revenue | hygiene.
- Owner: Compliance & RG Officer | CRM Manager | Backend Engineer |
  Fraud & AML Analyst.
- Link patterns: HOST is https://fly.customer.io (US) or
  https://eu.fly.customer.io (EU), from the region in `cio_auth_status`; WS
  is the workspace ID.

  | Object | URL |
  |---|---|
  | Automation | HOST/workspaces/WS/journeys/automations/ID/overview |
  | Broadcast | HOST/workspaces/WS/journeys/broadcasts/newsletter/ID |
  | Segment | HOST/workspaces/WS/journeys/segments/ID |
  | Segment people | HOST/workspaces/WS/journeys/segments/ID/people |
  | Frequency caps | HOST/workspaces/WS/settings/actions/message_frequency_limits |
- Docs: official docs.customer.io pages only, for example:

  | Topic | URL |
  |---|---|
  | Broadcasts | https://docs.customer.io/journeys/newsletters/ |
  | How segments work | https://docs.customer.io/messaging/segmentation/segments/ |
  | Data-driven segments | https://docs.customer.io/messaging/segmentation/data-driven-segments/ |
  | Exit conditions | https://docs.customer.io/journeys/send/campaigns/exit-conditions/ |
  | Automation settings | https://docs.customer.io/messaging/send/campaigns/overview/ |
  | Automation states | https://docs.customer.io/journeys/send/campaigns/statuses/ |
  | Set up frequency limits | https://docs.customer.io/messaging/send/message-limits/set-up-message-limits/ |
  | Subscription topics | https://docs.customer.io/messaging/channels/subscriptions/overview/ |
  | Subscription center | https://docs.customer.io/messaging/channels/subscriptions/center/ |
  | Webhook actions | https://docs.customer.io/messaging/send/workflows/webhooks/action/ |
  | Track API (identify) | https://docs.customer.io/api/track |
- Agent task: the fixed preamble below, then the steps; or `null` when the fix
  is a backend change, a compliance decision, or a start, stop, archive,
  send or delete.
- Agent task preamble: "Workspace WS (Customer.io REGION, ENVIRONMENT). Call
  cio_auth_status first and confirm WS is allowed; pass environment_id WS on
  every call. Read the named Customer.io skills with cio_skills_read before
  writing. GET every object you change in full first. Send every write with
  dry_run true, show me the preview, and wait for my explicit approval before
  executing. Never start, stop, schedule or archive an automation; never send,
  test-send or trigger anything; never call cio_delete_api; never write to
  people; never read or repeat secrets. When done, read each changed object
  back and report its ID, name and changed fields."
- Verify preamble (for the HTML copy button): "Read-only verification.
  Workspace WS. Call cio_auth_status, then use only cio_read_api (GET). Read
  full objects: a field is missing only when the API returns it empty. Decode
  action conditions (base64, then URL) before judging. Report PASS or FAIL per
  check with the value read, then FIXED, PARTLY FIXED or NOT FIXED."

## Next
Deliver the ledger, then run `protocols/self-refine.md` at the end of the
session. If the user approves fixes, start a new run with
`protocols/intake-plus.md` in BUILD mode. Offer SMOKE for the workspace's
suppression gate.

# Platform implementation (Customer.io, and translation to others)

Context: Customer.io build facts: workspace settings, naming, identify and
track patterns, integrations and SLAs, webhooks back, rate limits, testing,
governance and the phased build plan, plus a concept map for other platforms.
Read it for blueprint sections 5, 6 and 15, FLOW gate pieces, and audits.

## Contents
- Key idea
- Workspace settings
- Naming conventions
- People, identify and track
- Backend integrations and SLAs
- Webhooks back and counters
- Rate limits and volume
- Triggers and activation
- Live config access (LIVE-AUDIT and BUILD)
- Testing
- Governance and access
- Phased build plan
- Other platforms: primitive mapping table

## Key idea
Customer.io holds the profile, segments, journeys and templates; the backend
holds the truth for anything compliance-related and answers the L4 check. No
marketing journey goes live before the compliance phase (gate, L4, RG) is
signed off.

## Workspace settings
- One workspace with `regulatory_zone` branches for a single brand; separate
  workspaces per brand only when products differ materially.
- Time zone UTC; all timestamps compared in UTC; quiet hours applied per
  player zone where the market requires them.
- Global unsubscribe and topic unsubscribe on; hard-bounce suppression on;
  soft bounces suppressed after 3 consecutive; complaints auto-suppressed.
- Sending domain authenticated with SPF, DKIM and DMARC before first send;
  warm-up plan for new domains or IPs.

## Naming conventions
- Segments: `SEG_UPPER_SNAKE` (`SEG_CAN_RECEIVE_MARKETING`).
- Journeys (campaigns): `JRN_<TYPE>_<NN>_<Name>` (`JRN_MKT_03_No_Deposit_Activation`).
- Events: snake_case past tense (`deposit_successful`).
- Attributes: snake_case nouns (`rg_risk_level`).
- Topics: Casino Offers, Sportsbook Offers, VIP & Loyalty, Product Updates &
  Specials, Safer Gambling, Transactional.

## People, identify and track
People are keyed by `user_id` as the Customer.io `id`; email is secondary, so
an email change never splits a profile.
```json
{
  "type": "identify",
  "id": "player_12345",
  "attributes": {
    "email": "player@example.com",
    "country": "DE",
    "regulatory_zone": "DE",
    "email_verified": true,
    "email_marketing_consent": true,
    "kyc_status": "approved",
    "account_status": "active",
    "self_excluded": false,
    "rg_risk_level": "low"
  }
}
```
```json
{
  "name": "deposit_successful",
  "id": "player_12345",
  "data": {
    "amount": 100.00,
    "currency": "EUR",
    "deposit_number": 1,
    "completed_at": 1751234567
  }
}
```

## Backend integrations and SLAs
| System | Sends | SLA | Priority |
|---|---|---|---|
| Auth / registration | `identify` + `registered` | real time | critical |
| Email verification | `email_verified` | real time | critical |
| KYC | `identify` (`kyc_status`, `age_verified`) + `kyc_approved` / `kyc_rejected` | 5 min | critical |
| Payments | `deposit_started`, `deposit_successful`, `deposit_failed`, withdrawals | real time | critical |
| Game engine / sportsbook | `first_game_played`, `game_played`, `bet_placed` | real time | high |
| Bonus service | `bonus_*` events, `bonus_eligible`, `bonus_abuse_flag` | real time | high |
| RG model | `identify` (`rg_risk_level`) + `rg_signal_detected`, `rg_risk_escalated` | 15 min | critical |
| Self-exclusion / timeout | `identify` (`self_excluded`, `timeout_active`, `excluded_until`) + events | 5 min | critical |
| National registers | `identify` (`self_exclusion_register_match`, `self_exclusion_register`) | 5 min | critical |
| AML / fraud | `identify` (`aml_status`, `fraud_flag`) + events | 15 min | critical |
| Account service | `identify` (`account_status`) + events | 5 min | critical |
| Consent service | consent fields | real time | critical |
| Loyalty / VIP | `vip_tier`, `vip_status` + VIP events | 15 min | high |
| Finance and session analytics | aggregates | daily 02:00 UTC | high |
| Counter service | counters and cap flags | 1 h | high |
| Verify endpoint (L4) | answers the pre-send check | p95 under 200 ms | critical |

## Webhooks back and counters
Customer.io reporting webhooks go to the backend for delivered, opened,
clicked, unsubscribed, bounced, complained and converted. The delivered
webhook feeds the counter service; unsubscribed sets backend consent to false.
Reconciliation runs daily at 02:00 UTC (suppression gate reference).

## Rate limits and volume
Batch identify calls where possible (up to 1,000 per batch); use Customer.io
Data Pipelines for high-volume event streams; retry with exponential backoff;
monitor API error rates. Documented guidelines: Track and Pipelines about
3,000 requests per 3 seconds; App API 10 requests per second (transactional
messages are not rate limited); API-triggered broadcasts 1 request every 10
seconds. Per-automation send rate limits are a speed control, not a cap
(caps reference).

## Triggers and activation
- An event trigger takes one event. A journey with several causes triggers on
  one normalised event the backend sends with a `reason` field
  (`rg_intervention_required`, `account_notice_required`, `kyc_required`; event
  taxonomy), or on an attribute or segment trigger.
- Attribute and segment triggers cannot fire on "not in segment" alone.
- Activation: "only future additions" for reactivation and win-back
  automations; "current people and future additions" needs a written decision
  because it mails everyone who already matches on the day the automation
  starts. Date-triggered automations always include current matches.
- Exit conditions: by default a person exits when they stop matching the
  trigger or filter; custom exits (attributes, events, segments) are OR
  statements and may differ from the goal. `RG_EXIT_BLOCK` uses them.
- Wait Until blocks have Conditions, Delay, Event time and Max time paths;
  every Wait Until in this skill has a Max time path.

## Live config access (LIVE-AUDIT and BUILD)
LIVE-AUDIT (`protocols/live-audit.md`) pulls the live setup instead of asking
for an export, in this order, always read-only:
1. Official Customer.io MCP server: `https://mcp.customer.io/mcp` (EU
   `https://mcp-eu.customer.io/mcp`), transport `http`, each user signs in
   with their own Customer.io login. Reads (`cio_read_api`, GET only) are
   split from writes (`cio_write_api`) and deletes (`cio_delete_api`) so the
   connector can require approval for each; an audit uses reads only. Tools:
   `cio_schema` to find endpoints, `cio_read_api` to list automations,
   segments, topics and frequency caps, `cio_skills_list` /
   `cio_skills_read` for Customer.io's task-specific workflow guidance,
   `cio_auth_status`. In Claude Code or Cowork, the Customer.io plugin wraps
   the same server. BUILD uses the same server with `cio_write_api` under the
   rules in `references/workspace-safety.md`.
2. Official CLI for terminal agents: `npm install -g @customerio/cli`, `cio
   auth login`, then `cio api`. Service-account tokens have full access, so
   use a read-only user token for audits.
3. Fallback: the community read-only MCP `pipeworx-io/mcp-customer-io` with a
   scoped App API key; it is community code, so say so in the findings.
4. No tool access: ask the user for the export.
Record the source used in the findings' "Scope reviewed" line.

## Testing
Test Mode and Preview for every template, with a profile missing `first_name`
and one per zone. A dedicated test player with `self_excluded = true` must
receive zero marketing across all journeys and broadcasts (QA reference).

## Governance and access
- Role-based access: authors draft; only CRM managers and compliance approve
  publishing journeys or editing gate segments.
- Dual sign-off (marketing operations and compliance) on every marketing
  template and on any change to gate, suppression or cap logic.
- Change log of journey, segment and suppression edits mirrored to the audit store.
- Kill switch (QA reference) owned by CRM operations and compliance: set
  `marketing_blocked = true` for the affected scope, then stop each Layer-3
  automation and broadcast with "Force people to exit immediately".

## Phased build plan
| Phase | Scope | Exit criterion |
|---|---|---|
| 1. Data model and integration | Schema, identify and track for all events, topics, workspace settings, consent and preference centre, TXN_01 | All events validated against schema |
| 2. Compliance and suppression | Gate and suppression segments, `RG_EXIT_BLOCK`, frequency caps, all segments, SE and register webhooks, RG and AML pipelines, L4 endpoint, reconciliation, audit log | Gate QA cases pass; legal sign-off |
| 3. Core journeys | TXN_01, SVC_02, MKT_03-05, RG_12, SYS_13, SYS_14; copy review; soft launch at 10% | Journey QA passes; no leakage at 10% |
| 4. Advanced journeys | MKT_06-10, VIP_11, SYS_15, market overlays, cap counters | Full QA passes |
| 5. Optimisation | A/B programme, KPI reviews, compliance reviews, webhook audits, daily reconciliation | Ongoing |
Phase tasks carry owner, dependency and effort in days in blueprint section 15.

## Other platforms: primitive mapping table
State in the deliverable: "Platform translation is best effort from general
platform knowledge; verify each primitive in the platform's documentation."
The Customer.io column is documented; every other column sits under this
banner, copied into the deliverable:
"Verify in target platform: these mappings are unverified."
| Primitive | Customer.io (documented) | Braze (unverified) | Optimove (unverified) |
|---|---|---|---|
| Profile attribute | Person attribute | Custom attribute | Customer attribute |
| Event | track event | Custom event | Real-time event |
| Entry trigger | One event, or attribute / segment trigger; activation current+future or future only | Action-based or audience entry | Target group entry |
| Gate segment | Data-driven segment | Segment / filter | Target group |
| Wait | Time delay; Wait Until with Max time | Delay / Action Paths | Wait step |
| Branch | True/false and multi-split branches | Decision split | Split |
| Per-send check | Action condition + webhook action | Message-level filter + Connected Content | Pre-send rule |
| Exit | Custom exit conditions (OR) | Exit criteria | Exit rule |
| Cap | Frequency caps (named) + backend flags | Frequency capping | Frequency rules |
| Suppression | Attributes + `RG_EXIT_BLOCK` + L4; ESP email suppression optional | Segment exclusion | Exclusion group |
| Consent topics | Subscription topics + channel preferences | Subscription groups | Opt-in channels / preferences |
| Templating | Liquid (Customer.io tag list) | Liquid | Personalisation tags |
Verification path for Braze: the Braze MCP server (`https://mcp.braze.com/mcp`,
EU `https://mcp.braze.eu/mcp`, OAuth). It includes write tools, so connect it
with a read-only dashboard user. The architecture, gate, caps, priority and RG
rules do not change; only the primitives do.

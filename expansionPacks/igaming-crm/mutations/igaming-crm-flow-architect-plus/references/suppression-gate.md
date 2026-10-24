# Global suppression gate

Context: the single most important control in the architecture. Read it for
blueprint section 5, any FLOW gate piece, every marketing journey's entry,
action and exit conditions, and step 1 of every audit.

## Contents
- Key idea
- Message layers
- Canonical gate pseudocode
- Customer.io implementation layers L1-L4
- L4 pre-send check: request, response, branch
- Exit set on every marketing journey
- Self-exclusion SLA budget
- Backstops: reconciliation, audit log, downtime
- Accepted-risk variant (async quiet period)
- Gate QA cases

## Key idea
A marketing message reaches a player only if every gate condition holds at
entry, at every send, and continuously while the player waits inside the
journey. The defences, all mandatory for marketing:
1. Profile attributes (`self_excluded`, `self_exclusion_register_match`,
   `timeout_active`, `marketing_blocked`, with `self_exclusion_source`)
   feeding `SEG_CAN_RECEIVE_MARKETING` at entry and as action conditions.
2. `RG_EXIT_BLOCK` (`templates/rg-exit-block.md`) on every marketing automation.
3. The synchronous pre-send check (L4), which closes the window in which a
   self-exclusion written in the backend is still in flight to segments. Any
   error or missing answer blocks the send (fail safe).
Optional extra: ESP email suppression for self-excluded addresses. It stops
email only; other channels still send and the person still enters automations.

The never-suppress rule is SKILL.md hard rule 1. The calls it covers are Track
`POST /api/v1/customers/{id}/suppress` and Pipelines `User Suppressed`: both
delete the profile and its history and block the identifiers from being
re-added, which destroys the audit trail and stops the self-exclusion
confirmation and service mail.

## Message layers
| Layer | Scope | Gate | Consent | Caps | Unsubscribable |
|---|---|---|---|---|---|
| 1. RG / protective | Risk alerts, limit nudges, timeout and SE confirmations, spending summary | `SEG_CAN_RECEIVE_TRANSACTIONAL`; never the marketing gate | Not required | Exempt | No |
| 2. Transactional / service / system | Verification, KYC, receipts, password reset, preference confirmations, sunset notice | `SEG_CAN_RECEIVE_TRANSACTIONAL` | Not required; no promotional content | Exempt | No |
| 3. Marketing | Offers, bonuses, cross-sell, retention, reactivation, VIP | Full gate + topic + cap | Explicit, unbundled, withdrawable | Yes | Yes (topic and global) |

Priority between layers: RG over transactional over marketing.

## Canonical gate pseudocode
```text
function can_send(player, message):        # at entry, before EVERY send, and as exit
  if message.layer in {RG_PROTECTIVE, TRANSACTIONAL, SYSTEM}:
      return player.account_status != "closed" and player.email_verified == true
  # Layer 3 marketing: safety-critical first, short-circuit, log first failing reason
  block if player.marketing_blocked == true                      -> "marketing_blocked"
  block if player.self_excluded == true                          -> "self_excluded"
  block if player.self_exclusion_register_match == true          -> "self_excluded_register"
  block if player.timeout_active == true                         -> "timeout_active"
  block if player.rg_risk_level in {"high","severe"}             -> "rg_risk_suppressed"
  block if player.account_status != "active"                     -> "account_not_active"
  block if player.email_marketing_consent != true                -> "no_marketing_consent"
  block if player.email_verified != true                         -> "email_not_verified"
  block if player.age_verified != true                           -> "age_not_verified"
  block if player.kyc_status not in {"approved","provisional_allowed"} -> "kyc_incomplete"
  block if player.unsubscribed == true                           -> "globally_unsubscribed"
  block if player.country_license_status != "licensed"           -> "unlicensed_jurisdiction"
  block if player.aml_status in {"blocked","frozen","restricted"} -> "aml_restricted"
  block if player.fraud_flag == true                             -> "fraud_flagged"
  block if not subscribed(player, message.topic)                 -> "topic_unsubscribed"
  block if player.frequency_cap_reached == true                  -> "frequency_cap_reached"
  if message.is_bonus:
      block if player.bonus_abuse_flag == true or player.bonus_eligible != true -> "bonus_ineligible"
      block if player.rg_risk_level == "medium"                  -> "rg_medium_no_bonus"
      block if player.bonus_cap_reached == true                  -> "bonus_cap_reached"
      block if market_rule_blocks_bonus(player)                  -> "market_bonus_rule"
  if message.is_cross_sell:
      block if player.cross_sell_cap_reached == true             -> "cross_sell_cap_reached"
  if player.rg_risk_level == "medium":
      apply the rg_medium cap (1 per week); no urgency or loss-chasing content
  return ALLOW
```
The fourteen gate conditions are: marketing_blocked, self_excluded,
timeout_active, rg_risk_level high/severe, account_status,
email_marketing_consent, email_verified, age_verified, kyc_status,
unsubscribed, country_license_status, aml_status, fraud_flag, and the
frequency cap; the subscription topic is checked on top.
`frequency_cap_reached` is computed by the counter service from
`marketing_emails_sent_today`, `marketing_emails_sent_last_7d` and
`last_marketing_email_sent_at` against the most restrictive cap that applies
(see the caps reference). `market_rule_blocks_bonus` covers the bonus rules in
`references/markets.json`, for example the first-play-only market
(`regulatory_zone == "SE" AND first_play_bonus_used == true`).

## Customer.io implementation layers L1-L4
| Layer | Configuration | Catches |
|---|---|---|
| L1 | Data-driven `SEG_CAN_RECEIVE_MARKETING` (segment library); also the audience filter on every broadcast | Ineligible players at audience build |
| L2 | Journey entry condition: `Person is in segment SEG_CAN_RECEIVE_MARKETING` | Ineligible players at entry |
| L3 | Action condition on every email node: in `SEG_CAN_RECEIVE_MARKETING` AND not in `SEG_FREQUENCY_CAP_REACHED` (bonus emails: in `SEG_CAN_RECEIVE_BONUS`) | Status changes during waits |
| L4 | Webhook action immediately before every email: synchronous call to the backend verify endpoint, then a branch on the answer | The async window between backend write and segment update |

L4 and `RG_EXIT_BLOCK` are both required. No marketing journey goes live
before both are built and the gate QA cases pass.

## L4 pre-send check: request, response, branch
Request (webhook action, POST to `https://<backend-host>/crm/verify-suppression`,
bearer token of a dedicated CRM service account, timeout at most 30 s):
```json
{
  "user_id": "player_12345",
  "journey_id": "JRN_MKT_09_Churn_Prevention",
  "campaign_id": "cmp_8812",
  "message_type": "promotional",
  "topic": "casino_offers",
  "is_bonus": false,
  "requested_at": "2026-01-15T10:00:00Z"
}
```
In the webhook body, fill the values from Liquid: `{{ customer.id }}` for
`user_id` and the journey's own ID as a literal string.

Response (backend evaluates `can_send`, reading a cache keyed
`suppression:{user_id}` with TTL 300 s, invalidated synchronously on every SE,
timeout, RG or account-status write; falls back to the database on a miss):
```json
{
  "user_id": "player_12345",
  "can_receive_marketing": false,
  "can_receive_transactional": true,
  "suppression_reason": "self_excluded",
  "evaluated_at": "2026-01-15T10:00:00.120Z",
  "cache_hit": true
}
```
Branch: save `can_receive_marketing` from the response into the journey (or
person) data, then a true/false branch: `can_receive_marketing == true` goes to
the email; false, missing, HTTP error or timeout goes to exit with
`suppression_reason` logged. Targets: p95 latency under 200 ms, availability
99.9%, under 500 ms on database fallback. Confirm the exact response-capture
option in the workspace's webhook action before go-live.

## Exit set on every marketing journey
The exit set is `RG_EXIT_BLOCK`, kept in one place:
`templates/rg-exit-block.md` (attribute conditions for `marketing_blocked`,
`self_excluded`, register match, `timeout_active`, `rg_risk_level` high or
severe, account suspended or closed, AML restricted, `unsubscribed`, plus
membership of `SEG_RG_SUPPRESSED`). Every MKT and VIP spec writes
`RG_EXIT_BLOCK` in its exit cell (validator rule C22), plus the journey's own
lifecycle exit (conversion, supersession, timeout).

## Self-exclusion SLA budget
| Step | Action | Budget | Cumulative |
|---|---|---|---|
| T+0 | Player self-excludes (UI, support or register match) | 0 | 0 |
| T+1 | Backend writes `self_excluded = true` | under 1 s | under 1 s |
| T+2 | Backend invalidates the suppression cache key | under 1 s | under 2 s |
| T+3 | Backend sends `identify()` and `track("self_exclusion_started")` | under 5 s | under 7 s |
| T+4 | Customer.io updates the profile | under 30 s | under 40 s |
| T+5 | Attribute exits in `RG_EXIT_BLOCK` and segments fire | under 3 min | under 4 min |
| Gate | Fully suppressed on every channel | under 5 min | under 5 min |
L4 enforces suppression from T+1, independent of T+4 and T+5. The T+4 and T+5
budgets are design targets; Customer.io publishes no processing SLA for them
(verify before deployment).

## Backstops: reconciliation, audit log, downtime
- Daily reconciliation 02:00 UTC: backend suppression list (SE, timeout, RG
  high/severe, AML restricted) against `SEG_RG_SUPPRESSED` and
  `SEG_AML_RESTRICTED` membership; backend consent against Customer.io topic
  and unsubscribe state. Alert levels: `missing_in_cio > 0` CRITICAL, block
  all broadcasts until resolved; leakage rate above 0.1% HIGH; `extra_in_cio`
  above 5% MEDIUM (stale data); otherwise OK, logged.
- Audit log: append-only, tamper-evident store, retained 7 years. One record
  per suppression event (reason, source, write, cache and Customer.io
  timestamps, SLA elapsed, journeys exited) and one per L4 call (journey,
  decision, reason, latency, cache hit).
- Downtime: an L4 outage blocks every gated send automatically. Planned
  maintenance: pause Layer-3 broadcasts first. Outage over 30 minutes:
  compliance reviews blocked sends before any re-queue.

## Accepted-risk variant (async quiet period)
Allowed only when the operator accepts the residual risk in writing. L1-L3
stay; L4 is replaced by: a promotional quiet period of 60 minutes after any
change to a status-critical attribute (`self_excluded`, `timeout_active`,
`rg_risk_level`, `account_status`, `aml_status`, `unsubscribed`), implemented
as a wait plus re-check of `SEG_CAN_RECEIVE_MARKETING` before each email, and a
self-exclusion disclosure page shown to the player before confirming. The
output carries this flag verbatim:
"ACCEPTED-RISK VARIANT: the synchronous pre-send check is not implemented. A
residual window of up to the segment sync time exists in which a newly
suppressed player can receive marketing. Accepted in writing by the operator;
reference the acceptance record."

## Gate QA cases
| ID | Setup | Expected |
|---|---|---|
| QA_GATE_01 | `self_excluded = true` in backend | L4 returns false; no email |
| QA_GATE_02 | `timeout_active = true` | No email |
| QA_GATE_03 | `rg_risk_level = "high"` | No email |
| QA_GATE_04 | `aml_status = "blocked"` | No email |
| QA_GATE_05 | All conditions pass | Email delivered |
| QA_GATE_06 | Verify endpoint times out | Journey exit logged; no email |
| QA_GATE_07 | Verify endpoint returns HTTP 500 | No email |
| QA_GATE_08 | Player self-excludes during a wait step | Next L4 call blocks |
| QA_GATE_09 | Self-exclusion SLA timing | At most 300 s in the audit log |
| QA_GATE_10 | Suppressed in backend only | Reconciliation alert, `missing_in_cio = 1` |
| QA_GATE_11 | `marketing_blocked = true` on a profile inside a marketing journey | `RG_EXIT_BLOCK` exits it; no email; RG and transactional mail still delivered |

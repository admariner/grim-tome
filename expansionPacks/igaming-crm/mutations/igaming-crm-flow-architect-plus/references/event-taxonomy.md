# Event taxonomy

Context: the canonical events sent with Customer.io `track()`. Read it for
blueprint section 3, for every journey trigger and conversion event, and when
mapping an operator's own event names. The validator reads the event names in
the first column of these tables (rule C18).

## Contents
- Key idea
- Core events (31) by family
- Generic additions (10)
- Normalised trigger events (3)
- Conversion events
- Example payloads
- Webhooks Customer.io sends back
- Operator events

## Key idea
Events trigger journeys, feed segments and mark conversions. Names are
snake_case, past tense, and identical in backend code, segment conditions and
journey triggers. Every payload carries `user_id` as the Person `id`. A
Customer.io event trigger takes one event, so a journey with several causes
triggers on one normalised event that the backend sends alongside the source
event, with a reason field (table below).

## Core events (31) by family
| Event | Fires when | Required fields | Optional fields | Journeys | Conversion |
|---|---|---|---|---|---|
| `registered` | Registration form completed | user_id, email, country, regulatory_zone, registration_source | referral_code, affiliate_id, device_type | TXN_01 (trigger) | No |
| `email_verified` | Verification link clicked | user_id, email, verified_at | verification_method | TXN_01 | Yes |
| `kyc_started` | KYC upload begins | user_id, kyc_provider, started_at | document_type | SVC_02 | No |
| `kyc_approved` | KYC passes | user_id, kyc_status, approved_at | verification_level, documents_verified | SVC_02 (exit); MKT_03 starts from the segment it leads to | Yes |
| `kyc_rejected` | KYC fails | user_id, rejection_reason, rejected_at | resubmission_allowed | SVC_02 | No |
| `deposit_started` | Deposit initiated | user_id, amount, currency, payment_method, started_at | deposit_number, bonus_code | MKT_04 | No |
| `deposit_failed` | Deposit attempt fails | user_id, amount, currency, failure_reason, failed_at | payment_method, attempt_count | RG_12 (signal) | No |
| `deposit_successful` | Deposit completes | user_id, amount, currency, payment_method, deposit_number, completed_at | bonus_triggered, bonus_id | MKT_04, MKT_05, MKT_06 | Yes |
| `withdrawal_requested` | Withdrawal submitted | user_id, amount, currency, payment_method, requested_at | withdrawal_id | SVC_02, SYS_13 | No |
| `withdrawal_completed` | Withdrawal processed | user_id, amount, currency, completed_at | withdrawal_id, processing_time_hrs | SYS_13 | No |
| `first_game_played` | First ever game round | user_id, game_id, game_name, game_type, played_at | session_id, device_type | MKT_05 | Yes |
| `game_played` | Game session completes | user_id, game_id, game_name, game_type, session_duration_mins, played_at | net_result, session_id | MKT_08 | No |
| `bet_placed` | Sportsbook bet placed | user_id, bet_id, amount, currency, sport, event_id, placed_at | odds, bet_type, selection | MKT_07, MKT_08 | No |
| `bonus_claimed` | Bonus activated | user_id, bonus_id, bonus_type, bonus_value, claimed_at, expires_at | campaign_id, wagering_requirement | MKT_06 (trigger) | Yes |
| `bonus_progress_updated` | Wagering progress changes | user_id, bonus_id, progress_pct, updated_at | remaining_wagering, expiry_at | MKT_06 | No |
| `bonus_completed` | Wagering requirement met | user_id, bonus_id, completed_at, winnings_released | total_wagered | MKT_06 | Yes |
| `bonus_expired` | Bonus expires unfinished | user_id, bonus_id, expired_at, progress_pct_at_expiry | bonus_value_forfeited | MKT_06 | No |
| `limit_set` | Deposit, loss or session limit set | user_id, limit_type, limit_value, currency, set_at | previous_limit, cooldown_period | RG_12 | No |
| `limit_removed` | Limit removed or increased | user_id, limit_type, removed_at | previous_limit, new_limit | RG_12 (signal) | No |
| `responsible_gambling_page_visited` | Safer-gambling page visited | user_id, page_url, visited_at | referral_source, session_id | RG_12 (monitoring) | No |
| `rg_signal_detected` | RG model detects a signal | user_id, signal_type, risk_level, detected_at | signal_value, threshold | RG_12 | No |
| `rg_risk_escalated` | Risk level increases | user_id, previous_risk_level, new_risk_level, escalated_at | escalation_reason, triggered_by | RG_12, SYS_13 | No |
| `timeout_started` | Voluntary timeout begins | user_id, timeout_duration_days, started_at, ends_at | timeout_reason | RG_12 | No |
| `self_exclusion_started` | Player self-excludes or register match | user_id, exclusion_type, duration, started_at | register_name, exclusion_reason | RG_12 | No |
| `account_suspended` | Operator suspends account | user_id, suspension_reason, suspended_at | suspended_by, review_date | SYS_13 | No |
| `account_closed` | Account closed | user_id, closure_reason, closed_at | closure_type, gdpr_erasure_requested | SYS_13 | No |
| `fraud_or_bonus_abuse_flagged` | Fraud or abuse detected | user_id, flag_type, flagged_at | flagged_by, evidence_summary | SYS_13 | No |
| `aml_status_changed` | AML status changes | user_id, previous_status, new_status, changed_at | changed_by, case_id | SYS_13 | No |
| `unsubscribe_updated` | Topic or global preference changes | user_id, topic, action, updated_at | source, reason | SYS_14 | No |
| `vip_qualified` | VIP criteria met | user_id, vip_tier, qualified_at | qualifying_metric, qualifying_value | VIP_11 (conversion only) | Yes |
| `vip_status_changed` | VIP tier or status changes, including first qualification | user_id, previous_tier, new_tier, direction (up, down, host_assigned), changed_at | change_reason | VIP_11 (trigger; entry keys on direction and new_tier) | No |

## Generic additions (10)
| Event | Fires when | Required fields | Optional fields | Journeys | Conversion |
|---|---|---|---|---|---|
| `bonus_offer_expired` | An offered bonus's claim window ends without a claim | user_id, offer_id, expired_at | campaign_id | MKT_06 (exit) | No |
| `free_spins_awarded` | Free spins credited | user_id, bonus_id, spins_count, game_id, awarded_at | expiry_at | MKT_04, MKT_06 | No |
| `free_spins_completed` | All awarded spins used | user_id, bonus_id, completed_at | winnings_amount | MKT_06 | No |
| `sports_bet_settled` | Bet settles | user_id, bet_id, result, settled_at | payout_amount | MKT_08 | No |
| `casino_session_started` | Casino session opens | user_id, session_id, started_at | game_type | MKT_08 | No |
| `rg_loss_limit_triggered` | Loss limit reached | user_id, limit_value, currency, triggered_at | period | RG_12 | No |
| `rg_session_limit_reached` | Session time limit reached | user_id, limit_minutes, reached_at | session_id | RG_12 | No |
| `rg_reality_check_acknowledged` | Reality-check prompt answered | user_id, action, acknowledged_at | session_minutes | RG_12 (signal) | No |
| `password_reset_requested` | Password reset requested | user_id, requested_at | ip_country, device_type | SYS_13 | No |
| `security_alert_triggered` | New device, login anomaly | user_id, alert_type, triggered_at | ip_country | SYS_13 | No |

## Normalised trigger events (3)
The backend sends one of these next to each source event it covers; the source
events stay for segments, reporting and conversion.

| Event | Fires when | Required fields | Optional fields | Journeys | Conversion |
|---|---|---|---|---|---|
| `rg_intervention_required` | Any RG cause: `rg_risk_escalated`, `rg_signal_detected` at medium or above, `limit_removed`, `rg_loss_limit_triggered`, `rg_session_limit_reached`, `timeout_started`, `self_exclusion_started` | user_id, reason (risk_escalated, signal_detected, limit_removed, loss_limit, session_limit, timeout_started, self_exclusion_started), risk_level, occurred_at | source_event, signal_type | RG_12 (trigger) | No |
| `account_notice_required` | Any account or payment notice: `account_suspended`, `account_closed`, `aml_status_changed`, `fraud_or_bonus_abuse_flagged`, `password_reset_requested`, `security_alert_triggered`, `withdrawal_completed` | user_id, notice_type (password_reset, security_alert, withdrawal_completed, account_suspended, account_closed, aml_status_changed, fraud_or_bonus_abuse_flagged), occurred_at | amount, currency, requested_at | SYS_13 (trigger) | No |
| `kyc_required` | KYC is needed: `kyc_started`, `withdrawal_requested` before approval, or deposits above the operator's KYC threshold | user_id, reason (kyc_started, withdrawal_requested, deposit_threshold), occurred_at | upload_url, document_type | SVC_02 (trigger) | No |

## Conversion events
`email_verified`, `kyc_approved`, `deposit_successful` (first deposit when
`deposit_number == 1`), `first_game_played`, `bonus_claimed`, `bonus_completed`,
`vip_qualified`. Journeys may also convert on `bet_placed` or `limit_set`
(RG_12 outcome); name the event, not a prose goal.

## Example payloads
```json
{
  "name": "deposit_successful",
  "id": "player_12345",
  "data": {
    "amount": 100.00,
    "currency": "EUR",
    "payment_method": "card",
    "deposit_number": 1,
    "completed_at": 1751234567,
    "bonus_triggered": true,
    "bonus_id": "WELCOME_1"
  }
}
```

```json
{
  "name": "rg_risk_escalated",
  "id": "player_12345",
  "data": {
    "previous_risk_level": "low",
    "new_risk_level": "medium",
    "escalated_at": 1751234567,
    "escalation_reason": "deposit_velocity_spike",
    "triggered_by": "rg_model_v2"
  }
}
```

```json
{
  "name": "self_exclusion_started",
  "id": "player_12345",
  "data": {
    "exclusion_type": "permanent",
    "duration": null,
    "started_at": 1751234567,
    "register_name": "operator_internal",
    "exclusion_reason": "player_request"
  }
}
```

```json
{
  "name": "bonus_claimed",
  "id": "player_12345",
  "data": {
    "bonus_id": "RELOAD50",
    "bonus_type": "deposit_match",
    "bonus_value": 50.00,
    "claimed_at": 1751234567,
    "expires_at": 1753826567,
    "campaign_id": "CMP_RELOAD_Q3",
    "wagering_requirement": 35
  }
}
```

## Webhooks Customer.io sends back
| Event | Backend endpoint | Backend action |
|---|---|---|
| Email delivered | `/webhooks/customerio/delivered` | Increment frequency counters, set `last_marketing_email_sent_at` |
| Email opened | `/webhooks/customerio/opened` | Update `last_email_engagement_at` |
| Email clicked | `/webhooks/customerio/clicked` | Update `last_email_engagement_at` |
| Unsubscribed | `/webhooks/customerio/unsubscribed` | Set backend `email_marketing_consent = false` and `unsubscribed = true` |
| Hard bounce | `/webhooks/customerio/bounced` | Mark address invalid |
| Spam complaint | `/webhooks/customerio/complained` | Block marketing to the address, open an investigation |
| Journey converted | `/webhooks/customerio/converted` | Conversion reporting |

## Operator events
Ask for the operator's existing event names at intake. Map each to a canonical
event where the meaning matches (for example `user_registered` maps to
`registered`, `fiat_deposit_completed` and `crypto_deposit_completed` both map
to `deposit_successful` with a `payment_method` field). Product-specific events
with no canonical match (crash rounds, raffles, rakeback, esports) stay as
declared operator events, are listed in blueprint section 3 under "Operator
events", and go to the validator through `--events`.

# Segment library

Context: every canonical segment with exact logic. Read it for blueprint
section 4, any FLOW segment set, and the entry, exit and branch conditions of
journeys. All names follow `SEG_UPPER_SNAKE` (validator rule C05).

## Contents
- Key idea
- Logic syntax and Customer.io builder phrasing
- Registry (purpose, priority, journeys)
- Logic: gate and eligibility
- Logic: suppression
- Logic: lifecycle and onboarding
- Logic: activity, value and VIP
- Logic: product vertical
- Logic: churn, dormancy, reactivation
- Logic: channel and engagement
- Corrections applied to the source library

## Key idea
Every segment is a Customer.io data-driven segment that re-evaluates as
attributes change. Manual and CSV-upload segments are never used for anything
compliance-related. Gate and suppression segments are P0: they are built and
tested before any marketing journey exists.

## Logic syntax and Customer.io builder phrasing
Logic is written as `attribute operator value` joined by AND/OR, and
`IN SEG_X` for segment membership. Build it in the segment editor like this:

| Logic | Customer.io condition |
|---|---|
| `x == true` | Person attribute `x` is true |
| `x != true` | Person attribute `x` is not true (also matches unset) |
| `x == "v"` | Person attribute `x` is equal to `v` |
| `x IN ["a","b"]` | Person attribute `x` is one of `a`, `b` |
| `x NOT IN ["a","b"]` | Person attribute `x` is not one of `a`, `b` |
| `x >= n`, `x < n` | Person attribute `x` is greater than or equal to / less than `n` |
| `x BETWEEN a AND b` | two conditions: `x >= a` AND `x <= b` |
| `t > N days ago` | timestamp attribute `t` is within the last N days |
| `t < N days ago` | timestamp attribute `t` is more than N days ago |
| `IN SEG_X` | Person is in segment `SEG_X` |

Never write `attr_a > attr_b`: segments and event filters cannot compare two
attributes (validator rule C24). Compute the comparison in the backend and send
it as its own attribute (`loss_velocity_flag`, `deposit_spike_flag`). The Liquid
comparison workaround controls content only, never eligibility.

## Registry
| Segment | Family | Priority | Purpose | Used by |
|---|---|---|---|---|
| `SEG_CAN_RECEIVE_MARKETING` | Gate | P0 | Master marketing eligibility | Entry and action condition on every MKT/VIP journey; broadcast audience filter |
| `SEG_CAN_RECEIVE_TRANSACTIONAL` | Gate | P0 | Service, RG and system mail | TXN_01, SVC_02, RG_12, SYS_13-15 |
| `SEG_CAN_RECEIVE_BONUS` | Gate | P1 | Marketing-eligible and bonus-eligible | Bonus steps in MKT_03, MKT_04, MKT_06, MKT_09, MKT_10, VIP_11 |
| `SEG_RG_SUPPRESSED` | Suppression | P0 | No promotional contact | Exit on every MKT/VIP journey |
| `SEG_SELF_EXCLUDED` | Suppression | P0 | Operator or register self-exclusion | Exit set; RG_12 confirmation |
| `SEG_TIMEOUT_ACTIVE` | Suppression | P0 | Active cooling-off | Exit set |
| `SEG_AML_RESTRICTED` | Suppression | P0 | AML or fraud hold | Exit set; SYS_13 |
| `SEG_UNSUBSCRIBED` | Suppression | P0 | Global marketing opt-out | Exit set; SYS_14 |
| `SEG_COUNTRY_NOT_LICENSED` | Suppression | P0 | No licence for player's country | Hard block on marketing |
| `SEG_UNDERAGE_RISK` | Suppression | P0 | Age not verified | Hard block on marketing |
| `SEG_BONUS_ABUSE_SUPPRESSED` | Suppression | P1 | Bonus abuse | Excluded from bonus steps |
| `SEG_FREQUENCY_CAP_REACHED` | Suppression | P1 | Any marketing cap hit | Action-condition exclusion |
| `SEG_RG_MEDIUM` | RG | P0 | Medium risk: 1 promo/week, no bonuses | Cap row rg_medium; RG_12 |
| `SEG_HIGH_INTENSITY` | RG | P0 | Elevated play, RG monitoring | RG_12 monitoring |
| `SEG_NEW_REGISTRANT` | Lifecycle | P1 | Registered within 24h | TXN_01, MKT_03 |
| `SEG_KYC_INCOMPLETE` | Lifecycle | P1 | KYC outstanding, recent registrant | SVC_02 |
| `SEG_NO_DEPOSIT_ELIGIBLE` | Lifecycle | P1 | Verified, never deposited, marketing-eligible (includes the gate) | MKT_03 trigger and entry |
| `SEG_FIRST_DEPOSITOR` | Lifecycle | P1 | One deposit, within 7 days | MKT_04 |
| `SEG_FIRST_DEPOSIT_NO_PLAY` | Lifecycle | P1 | Deposited, not played | MKT_05 |
| `SEG_ACTIVE_CASUAL` | Activity | P2 | 1-4 sessions in 30 days | MKT_08 |
| `SEG_ACTIVE_CORE` | Activity | P1 | Regular weekly player | MKT_08, VIP_11 |
| `SEG_HIGH_ROLLER` | Value | P1 | High 30-day GGR | Cap row vip/high_roller |
| `SEG_VIP_ELIGIBLE` | VIP | P1 | Meets VIP threshold, not yet VIP | VIP_11 |
| `SEG_CASINO_ONLY` | Vertical | P2 | Casino bets only (90d) | MKT_07 |
| `SEG_SPORTSBOOK_ONLY` | Vertical | P2 | Sports bets only (90d) | MKT_07 |
| `SEG_CROSS_SELL_CASINO_TO_SPORTS` | Vertical | P2 | Casino player, cross-sell eligible | MKT_07 |
| `SEG_CROSS_SELL_SPORTS_TO_CASINO` | Vertical | P2 | Sports player, cross-sell eligible | MKT_07 |
| `SEG_CROSS_SELL_ELIGIBLE` | Vertical | P2 | Either cross-sell direction | MKT_07 trigger and exit |
| `SEG_CHURN_RISK` | Churn | P1 | 14-29 days since last bet | MKT_09 |
| `SEG_DORMANT_ANY` | Churn | P2 | 30-89 days (one ladder) | MKT_10 exit |
| `SEG_DORMANT_REACHABLE` | Churn | P2 | Dormant 30-89 days and marketing-eligible | MKT_10 trigger |
| `SEG_DORMANT_30` | Churn | P2 | 30-59 days | MKT_10 tier branch |
| `SEG_DORMANT_60` | Churn | P2 | 60-89 days | MKT_10 tier branch |
| `SEG_DORMANT_90` | Churn | P3 | 90+ days | SYS_15 |
| `SEG_REACTIVATION_ELIGIBLE` | Churn | P2 | Dormant and bonus-eligible | MKT_10 offer branch |
| `SEG_EMAIL_ENGAGED` | Channel | P3 | Opened or clicked within 30 days | Reporting, send-time tests |
| `SEG_EMAIL_UNENGAGED` | Channel | P3 | No engagement for 60+ days | SYS_15 |
| `SEG_SMS_OPTED_IN` | Channel | P2 | SMS marketing consent | SMS cap row |
| `SEG_PUSH_OPTED_IN` | Channel | P2 | Push permission | Push channel steps |
| `SEG_CONSENT_CASINO_EMAIL` | Channel | P0 (UK) | Casino email opt-in (product x channel) | UK casino email action condition |
| `SEG_CONSENT_BETTING_EMAIL` | Channel | P0 (UK) | Betting email opt-in (product x channel) | UK sportsbook email action condition |

## Logic: gate and eligibility
```text
SEG_CAN_RECEIVE_MARKETING := email_verified == true AND email_marketing_consent == true
  AND unsubscribed != true AND age_verified == true
  AND kyc_status IN ["approved","provisional_allowed"]
  AND country_license_status == "licensed" AND account_status == "active"
  AND self_excluded != true AND self_exclusion_register_match != true
  AND timeout_active != true
  AND rg_risk_level NOT IN ["high","severe"]
  AND aml_status NOT IN ["blocked","frozen","restricted"]
  AND fraud_flag != true AND sunset_suppressed != true
  AND marketing_blocked != true
SEG_CAN_RECEIVE_TRANSACTIONAL := account_status != "closed" AND email_verified == true
SEG_CAN_RECEIVE_BONUS := IN SEG_CAN_RECEIVE_MARKETING AND bonus_eligible == true
  AND bonus_abuse_flag != true AND kyc_status == "approved" AND rg_risk_level == "low"
```
The segment carries every attribute condition of the fourteen-condition gate
canon, including the `marketing_blocked` kill switch; the remaining one, the
frequency cap, is enforced by frequency caps, the action condition and L4,
plus `self_exclusion_register_match != true`, which mirrors the gate's register
check and `SEG_RG_SUPPRESSED`, so a register-matched player is blocked at L1-L3
and not only at L4. `sunset_suppressed` is a hygiene addition (set by
JRN_SYS_15). Topic subscription is enforced by the journey's topic setting and
the L4 check.
`SEG_CAN_RECEIVE_TRANSACTIONAL` deliberately has no `self_excluded` condition:
self-excluded players still receive the SE confirmation and service mail.

Closure exception: the account-closed notice (SYS_13) is legally required but
the closed status reaches the profile through `identify()` before the
`account_closed` event, which already removes the player from
`SEG_CAN_RECEIVE_TRANSACTIONAL`. That one email therefore uses the action
condition `email_verified == true` only, and nothing else in the workspace
may use it.

Verification exception: TXN_01 mails an address that is not verified yet, so
it cannot pass `SEG_CAN_RECEIVE_TRANSACTIONAL`. Its first email uses the
action condition `account_status != "closed" AND self_excluded != true AND self_exclusion_register_match != true AND timeout_active != true`; the reminder also requires
`account_status NOT IN ["suspended","restricted","closed"] AND self_excluded
!= true AND self_exclusion_register_match != true AND timeout_active != true`,
and the same three RG attributes are custom exits, so a self-excluded,
register-matched or timed-out player never gets the reminder. No other
journey may use this exception.

## Logic: suppression
```text
SEG_RG_SUPPRESSED := rg_risk_level IN ["high","severe"] OR self_excluded == true
  OR self_exclusion_register_match == true OR timeout_active == true
  OR account_status IN ["suspended","closed"]
SEG_SELF_EXCLUDED := self_excluded == true OR self_exclusion_register_match == true
SEG_TIMEOUT_ACTIVE := timeout_active == true AND excluded_until > now
SEG_AML_RESTRICTED := aml_status IN ["blocked","frozen","restricted"] OR fraud_flag == true
SEG_UNSUBSCRIBED := unsubscribed == true
SEG_COUNTRY_NOT_LICENSED := country_license_status != "licensed"
SEG_UNDERAGE_RISK := age_verified != true
SEG_BONUS_ABUSE_SUPPRESSED := bonus_abuse_flag == true
SEG_FREQUENCY_CAP_REACHED := frequency_cap_reached == true
SEG_RG_MEDIUM := rg_risk_level == "medium"
SEG_HIGH_INTENSITY := sessions_last_7d >= 5 OR deposits_last_7d >= 4
  OR session_duration_avg_mins >= 120
```

## Logic: lifecycle and onboarding
```text
SEG_NEW_REGISTRANT := registered_at > 1 days ago AND account_status == "active"
SEG_KYC_INCOMPLETE := kyc_status NOT IN ["approved","provisional_allowed"]
  AND account_status == "active" AND registered_at > 90 days ago
SEG_NO_DEPOSIT_ELIGIBLE := lifetime_deposits == 0 AND kyc_status == "approved"
  AND IN SEG_CAN_RECEIVE_MARKETING
SEG_FIRST_DEPOSITOR := lifetime_deposits == 1 AND first_deposit_at > 7 days ago
SEG_FIRST_DEPOSIT_NO_PLAY := lifetime_deposits >= 1 AND last_play_at is not set
  AND first_deposit_at < 1 days ago
```
Read `t > N days ago` as "within the last N days" (see the syntax table).

## Logic: activity, value and VIP
```text
SEG_ACTIVE_CASUAL := days_since_last_play <= 30 AND sessions_last_30d BETWEEN 1 AND 4
  AND lifetime_deposits >= 1
SEG_ACTIVE_CORE := days_since_last_play <= 14 AND sessions_last_30d >= 5
  AND deposits_last_30d >= 2
SEG_HIGH_ROLLER := ggr_last_30d >= HIGH_ROLLER_GGR_30D
SEG_VIP_ELIGIBLE := ggr_last_90d >= VIP_GGR_90D AND deposits_last_30d >= 5
  AND vip_status == "standard" AND IN SEG_CAN_RECEIVE_MARKETING
```
`VIP_GGR_90D` and `HIGH_ROLLER_GGR_30D` are operator-supplied thresholds in the
operator's currency, collected at intake. In a deliverable, write the number
(for example `ggr_last_90d >= 500`) and state where it came from.

## Logic: product vertical
```text
SEG_CASINO_ONLY := casino_bets_last_90d >= 1 AND sports_bets_last_90d == 0
SEG_SPORTSBOOK_ONLY := sports_bets_last_90d >= 1 AND casino_bets_last_90d == 0
SEG_CROSS_SELL_CASINO_TO_SPORTS := IN SEG_CASINO_ONLY AND IN SEG_CAN_RECEIVE_MARKETING
  AND days_since_last_play <= 30
SEG_CROSS_SELL_SPORTS_TO_CASINO := IN SEG_SPORTSBOOK_ONLY AND IN SEG_CAN_RECEIVE_MARKETING
  AND days_since_last_play <= 30
SEG_CROSS_SELL_ELIGIBLE := IN SEG_CROSS_SELL_CASINO_TO_SPORTS OR IN SEG_CROSS_SELL_SPORTS_TO_CASINO
```
MKT_07 triggers on entering and exits on leaving `SEG_CROSS_SELL_ELIGIBLE`, so
its exit is the same for both directions.

## Logic: churn, dormancy, reactivation
```text
SEG_CHURN_RISK := days_since_last_bet >= 14 AND days_since_last_bet < 30
SEG_DORMANT_30 := days_since_last_bet >= 30 AND days_since_last_bet < 60
SEG_DORMANT_60 := days_since_last_bet >= 60 AND days_since_last_bet < 90
SEG_DORMANT_90 := days_since_last_bet >= 90
SEG_DORMANT_ANY := days_since_last_bet >= 30 AND days_since_last_bet < 90
SEG_DORMANT_REACHABLE := IN SEG_DORMANT_ANY AND IN SEG_CAN_RECEIVE_MARKETING
SEG_REACTIVATION_ELIGIBLE := (IN SEG_DORMANT_30 OR IN SEG_DORMANT_60 OR IN SEG_DORMANT_90)
  AND IN SEG_CAN_RECEIVE_BONUS
```
`SEG_DORMANT_ANY` is the single dormant ladder: a player stays in it from day
30 to day 89, so tier changes never re-trigger anything. MKT_10 triggers on
the combined `SEG_DORMANT_REACHABLE`, so a player who becomes marketing-eligible
partway through dormancy is picked up when eligibility arrives; a trigger on
the dormant segment alone fires only once, at day 30.
An operator that scores churn may add `AND churn_risk_score >= 0.7` to
`SEG_CHURN_RISK`; keep the day window so the segment works without the model.

## Logic: channel and engagement
```text
SEG_EMAIL_ENGAGED := last_email_engagement_at > 30 days ago AND unsubscribed != true
SEG_EMAIL_UNENGAGED := (last_email_engagement_at < 60 days ago OR last_email_engagement_at is not set)
  AND registered_at < 60 days ago
SEG_SMS_OPTED_IN := sms_marketing_consent == true AND IN SEG_CAN_RECEIVE_MARKETING
SEG_PUSH_OPTED_IN := push_opt_in == true AND IN SEG_CAN_RECEIVE_MARKETING
SEG_CONSENT_CASINO_EMAIL := consent_casino_email == true
SEG_CONSENT_BETTING_EMAIL := consent_betting_email == true
```
UK journeys add the product's consent segment to the email action condition on
each product branch; `marketing_blocked` is a kill switch, not an RG state, so
`SEG_RG_SUPPRESSED` does not include it.

## Corrections applied to the source library
- `SEG_KYC_INCOMPLETE` targets players registered within the last 90 days (the
  source condition selected players registered more than 90 days ago).
- `SEG_VIP_ELIGIBLE` uses an operator threshold instead of a fixed amount, and
  `vip_status == "standard"` instead of `!= "vip"` so host-managed players are
  excluded too.
- `SEG_CAN_RECEIVE_BONUS` adds `rg_risk_level == "low"` so medium-risk players
  never receive bonuses even when a journey forgets the medium check.
- `SEG_RG_SUPPRESSED` adds closed accounts and register matches, and
  `SEG_CAN_RECEIVE_MARKETING` excludes register matches to stay consistent.
- `SEG_FIRST_DEPOSIT_NO_PLAY` uses `last_play_at is not set` rather than a
  30-day session count, which also matched lapsed players.
- `SEG_EMAIL_UNENGAGED` also matches profiles where `last_email_engagement_at`
  was never set (players who never opened or clicked).

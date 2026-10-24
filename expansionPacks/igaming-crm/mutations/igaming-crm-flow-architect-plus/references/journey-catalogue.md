# Journey catalogue

Context: the 15 canonical journeys, the ID pattern, the 16 spec dimensions, the
timing rule with worked checks, the flow-table columns and the Gate codes. Read
it for blueprint sections 7-8 and every FLOW journey; the full specs and flow
tables are in the three journey-flows references (onboarding, engagement,
protective).

## Contents
- Key idea
- ID pattern and types
- Catalogue (15 journeys)
- The 16 spec dimensions
- Timing rule
- Timing checks (MKT_03, MKT_04, MKT_07, MKT_08, MKT_10)
- Flow-table columns and Gate codes
- Guardrail metrics
- Compliance notes per journey

## Key idea
Each journey has one type, one topic, one cap rule and one gate. Marketing
journeys (MKT, VIP) use the full gate; RG, TXN, SVC and SYS journeys use the
transactional gate, are cap-exempt and carry no offers.

## ID pattern and types
`JRN_<TYPE>_<NN>_<Name>`, for example `JRN_MKT_09_Churn_Prevention`. Types:
TXN transactional, SVC service, MKT marketing, VIP VIP marketing, RG
responsible gambling, SYS system. Inside the catalogue table the short form
(`MKT_09`) is accepted; everywhere else use the full ID.

## Catalogue (15 journeys)
Gate column: MKT = full marketing gate; BONUS = MKT plus `SEG_CAN_RECEIVE_BONUS`
on bonus steps; TXN = `SEG_CAN_RECEIVE_TRANSACTIONAL`. Every MKT and VIP row
also carries `RG_EXIT_BLOCK` (`templates/rg-exit-block.md`). Every event
trigger names one event; journeys with several causes use a normalised event
(event taxonomy) or a segment trigger.

| ID | Name | Trigger | Entry | Exit (beyond `RG_EXIT_BLOCK`) | Topic | Gate | Cap (segment: daily/weekly) | Waits | Conversion |
|---|---|---|---|---|---|---|---|---|---|
| TXN_01 | Email Verification | `registered` | `email_verified != true` (`account_status` lags the event: checked after the first wait) | `email_verified == true`; account suspended, restricted or closed; `self_excluded`, `self_exclusion_register_match` or `timeout_active` true | Transactional | TXN (verification exception, with RG conditions on the reminder) | Exempt | 0, 24h, 48h, then flag | `email_verified` |
| SVC_02 | KYC Completion | normalised `kyc_required` (reason: kyc_started, withdrawal_requested, deposit_threshold) | `kyc_status NOT IN ["approved","provisional_allowed"]` | `kyc_approved` after the trigger, account suspended, or 7 d | Transactional | TXN | Exempt | 0, 24h, 48h | `kyc_approved` |
| MKT_03 | No-Deposit Activation | enters `SEG_NO_DEPOSIT_ELIGIBLE` (never deposited AND KYC approved AND in the marketing gate; fires after `kyc_status` syncs and picks up late-eligible players); activation: only future additions | `IN SEG_NO_DEPOSIT_ELIGIBLE` (includes `SEG_CAN_RECEIVE_MARKETING`) | `deposit_successful` or 14 d | Casino or Sportsbook Offers by product | BONUS | new_registrant 1/3 | 2h, 48h, 72h | `deposit_successful` |
| MKT_04 | First Deposit Welcome | `deposit_successful` with `event.deposit_number == 1` | `event.deposit_number == 1` (trigger payload) | second deposit or 7 d | Casino or Sportsbook Offers | BONUS | first_depositor 1/4 (MKT_04 uses 3) | 0, 24h, 72h | `deposit_successful` (n=2), `first_game_played` |
| MKT_05 | First-Play Activation | enters `SEG_FIRST_DEPOSIT_NO_PLAY` | `IN SEG_FIRST_DEPOSIT_NO_PLAY` | `first_game_played`, `bet_placed`, or 7 d | by product | MKT | first_depositor 1/4 (MKT_05 uses the fourth slot, one email) | 36h | `first_game_played` |
| MKT_06 | Bonus Lifecycle | `bonus_claimed` (progress path); the offer itself goes out as a reviewed API-triggered broadcast sharing the templates | `IN SEG_CAN_RECEIVE_BONUS`, not dormant | `bonus_completed`, `bonus_expired` | Casino or Sportsbook Offers | BONUS | active segment cap 1/2 or 1/4; bonus sub-limit | 0, until progress 50% (max 30 d) | `bonus_completed` |
| MKT_07 | Cross-Sell Casino and Sports | enters `SEG_CROSS_SELL_ELIGIBLE` | `IN SEG_CROSS_SELL_ELIGIBLE` (direction by branch) | leaves `SEG_CROSS_SELL_ELIGIBLE` (converted or inactive), or 7 d | target vertical's topic | MKT | active_core 1/4; cross-sell sub-limit | 0, 96h | `bet_placed` or `first_game_played` in new vertical |
| MKT_08 | Active Retention | schedule every 14 days for `SEG_ACTIVE_CASUAL` and `SEG_ACTIVE_CORE`, one active instance | in either segment AND `days_since_last_play <= 10` | `days_since_last_play > 14` or enters `SEG_CHURN_RISK` | Casino or Sportsbook Offers | MKT | active_casual 1/2, active_core 1/4 | 0, 7 d, 6 d | `deposit_successful`, session |
| MKT_09 | Churn Prevention | enters `SEG_CHURN_RISK`; activation: only future additions | `IN SEG_CHURN_RISK` | any wager (`bet_placed`, `game_played`) or `deposit_successful` after the trigger, `days_since_last_bet < 14`, or enters `SEG_DORMANT_30` | Casino or Sportsbook Offers | BONUS | churn_risk 1/2 (emails days 0, 4, 8 so the rolling 7-day window never holds three) | 0, 4 d, 4 d | `deposit_successful`, `bet_placed`, `game_played` |
| MKT_10 | Dormant Reactivation | enters `SEG_DORMANT_REACHABLE` (dormant 30-89 days AND marketing-eligible); one active instance; activation: only future additions (launch backfill only as a reviewed broadcast) | `IN SEG_DORMANT_REACHABLE`, routed by tier at entry; offer needs `SEG_REACTIVATION_ELIGIBLE` | any wager (`bet_placed`, `game_played`) or `deposit_successful` after the trigger, or leaves `SEG_DORMANT_ANY` (back under 30 days, or day 90: SYS_15 takes over) | Casino or Sportsbook Offers | BONUS | dormant_30 1/1, dormant_60 1/1 (cooldowns 48h, 336h) | 0, until `IN SEG_DORMANT_60` (max 35 d) | `deposit_successful` |
| VIP_11 | VIP Lifecycle | `vip_status_changed` (qualification is a conversion, not a trigger) | from the payload: `event.direction IN ["up","host_assigned"] AND event.new_tier != "none"` (downgrades never enter) | tier downgrade, `rg_risk_level != "low"` | VIP & Loyalty | BONUS (RG overrides VIP) | vip/high_roller 1/5 | 0, 14 d, 30 d | `deposit_successful` within 30 d |
| RG_12 | RG Intervention | normalised `rg_intervention_required` (reason, risk_level), sent by the backend for every RG cause | from the payload: `event.risk_level IN ["medium","high","severe"]`, or `event.reason` SE, timeout or a limit reason at any risk level | reviewed back to low; limit-event branch exits after its email; SE keeps permanent suppression | Safer Gambling | TXN (never marketing-suppressed) | Exempt | 0 (24h medium, 2h high), 7 d review | `limit_set`, `timeout_started`, `self_exclusion_started` |
| SYS_13 | Account and Compliance Status | normalised `account_notice_required` (notice_type) | the event | after send | Transactional | TXN (closure notice: closure exception) | Exempt | immediate | n/a |
| SYS_14 | Preference Confirmation | `unsubscribe_updated` | the event | after send | Transactional | TXN | Exempt | immediate | n/a |
| SYS_15 | Sunset and List Hygiene | in `SEG_DORMANT_90` and `SEG_EMAIL_UNENGAGED`; sole owner of the day-90 "keep hearing from us" email | both segments | engagement, or flag set | Transactional | TXN, no offers | Exempt | 0, 7 d | `email_verified` re-confirm or click |

## The 16 spec dimensions
In this order, as rows of a `| Dimension | Specification |` table:
journey_id, type, trigger, entry_conditions, exit_conditions,
subscription_topic, suppression_checks, frequency_cap, flow_steps, wait_times,
branch_logic, email_purpose, personalisation_fields, conversion_event,
guardrail_metrics, compliance_notes.

Rules the validator applies (C03-C09, C22, C25): all 16 filled; MKT/VIP entry
names `SEG_CAN_RECEIVE_MARKETING` and exit names `SEG_RG_SUPPRESSED` and
`RG_EXIT_BLOCK`; a trigger names one event; MKT/VIP topic is
a marketing topic and the cap is numeric; RG/TXN/SVC/SYS topic is
non-marketing and the cap is Exempt; every Email row whose purpose or subject
describes an offer (bonus, free spins, reload, free bet, cashback, offer)
carries Gate `BONUS`, and a journey with bonus content references
`SEG_CAN_RECEIVE_BONUS`, `bonus_abuse_flag` or the `BONUS` code.

## Timing rule
Checked by hand, not by the validator. Walk each journey as a player who
enters on day 0 of its trigger window and confirm every branch and email
condition is true when that player reaches it:
- Entry conditions read only data that exists at trigger time. An attribute on
  the daily batch is not yet updated when a real-time event fires; key entry
  on the event payload (`event.deposit_number == 1`) or on a real-time field.
  This holds for every event-triggered journey: entry and first-step
  decisions come from the payload (`event.reason`, `event.risk_level`,
  `event.direction`); an attribute with a 5-minute or slower SLA is read only
  after a wait long enough for it to sync, or with an explicit "attribute may
  lag" note.
- The entry window is never wider than the exit window: a player admitted on
  entry must not already meet an exit condition.
- A wait that must carry a player into another segment window (30 to 60 days)
  is a wait-until on that segment with a maximum, not a fixed delay.
- Every Wait Until has a Max time path with a fixed duration (`max 35 d`);
  without one a player can wait forever (validator rule C23). A player who
  already meets the wait condition on arrival skips the wait.
- Event conditions in waits, branches and exits are bounded to this journey:
  the event's timestamp is after the trigger event's timestamp (or "since
  entering the automation"); otherwise a past wager or deposit satisfies the
  condition at once and the wait or exit fires at entry.
- Activation: reactivation and win-back automations (MKT_09, MKT_10) start
  with "only future additions"; "current and future" needs a written decision
  because it mails everyone who already matches on the day it starts.
- A journey over several segments of one ladder triggers on one ladder segment
  (for example `SEG_DORMANT_ANY`) with one active instance, so re-entry only
  happens on a new episode, and branches by tier at entry.
- Exit conditions apply to every person in the journey. Never write exits that
  depend on which branch a person is on; exit on leaving the entry segment
  instead, or split the journey.
- Every journey exits on the behaviour it is trying to cause, on every vertical
  (a casino wager is `game_played`; `bet_placed` is sportsbook only).
- One journey owns each message: when two journeys could send the same kind of
  email to the same player at the same point, give one ownership.

## Timing checks (MKT_03, MKT_04, MKT_07, MKT_08, MKT_10)
MKT_03 No-Deposit Activation:
- Day 0: `kyc_approved` fires first; `kyc_status == "approved"` reaches the
  profile within 5 minutes, and only then does the player enter
  `SEG_NO_DEPOSIT_ELIGIBLE`, which is the trigger. Entry therefore never
  reads a value older than the trigger, and no branch re-checks eligibility.
  A player who gains marketing consent days later enters the combined segment
  at that moment and is picked up.
- Emails at about 2h, day 2 and day 5 fit the new_registrant cap (3 per week,
  24h cooldown); a deposit after the trigger exits the player.

MKT_04 First Deposit Welcome:
- Cap budget: first_depositor allows 4 per week; MKT_04 sends at most 3
  (days 0, 1, 4) and MKT_05 one (about day 2.5, 36h clear of each), so
  neither journey's email is skipped by the cap or the 24h cooldown.
- Day 0: the first `deposit_successful` arrives with `deposit_number = 1`;
  entry reads the payload, so it passes even though windowed aggregates update
  overnight. `lifetime_deposits` and `first_deposit_at` sync in real time
  (identify before track), so the 7-day cap segment `SEG_FIRST_DEPOSITOR` is
  also correct at day 0.
- Step 1 (day 0): branch on `SEG_CAN_RECEIVE_BONUS`, bonus or plain welcome.
- Step 3 (day 1): `active_bonus_id` is set in real time by the bonus service.
- Step 6 (day 4); exit on the second `deposit_successful` or at day 7. Every
  step falls inside the 7-day window.

MKT_07 Cross-Sell:
- Day 0: the daily batch puts the player in `SEG_CASINO_ONLY` or
  `SEG_SPORTSBOOK_ONLY` and, if active within 30 days and marketing-eligible,
  in `SEG_CROSS_SELL_ELIGIBLE`; entry fires.
- Step 1 branches by direction; steps 2 or 3 send on day 0.
- If the player converts (a wager in the other vertical), the next batch moves
  them out of the single-vertical segment, so they leave
  `SEG_CROSS_SELL_ELIGIBLE` and exit within about 24 hours. A wager in their
  own vertical changes nothing, so it does not exit them early.
- Step 5 (day 4) re-checks `IN SEG_CROSS_SELL_ELIGIBLE` (a conversion inside
  the batch lag is caught by the branch) and `SEG_CAN_RECEIVE_BONUS`; exit at day 7.

MKT_08 Active Retention:
- Day 0: the 14-day schedule admits players in `SEG_ACTIVE_CASUAL` or
  `SEG_ACTIVE_CORE` with `days_since_last_play <= 10`, so nobody is admitted
  already past the `> 14` exit or close to day 14, where `SEG_CHURN_RISK` begins.
- Step 3 (run day 7) sends only while `days_since_last_play <= 10`; anyone who
  crossed 14 days has already exited and is in MKT_09.
- Collision with MKT_09: an MKT_08 email always lands at 10 or fewer days
  since last play, so MKT_09's day-14 email sees at most one MKT_08 email in
  its rolling 7-day window (2 of 2 allowed), and the day-18 window (days
  11-18) holds only the day-14 email. A player at days 11-13 simply gets no
  MKT_08 email.
- Step 4 ends the run at day 13, before the next run starts on day 14.

MKT_10 Dormant Reactivation: the worked check is in the engagement flows
reference, next to the flow table.

## Flow-table columns and Gate codes
Columns: Step, Action, Wait, Branch condition, Gate, Subject approach, Content
purpose, Personalisation, Exit trigger. Action is one of Email, Wait, Branch,
Webhook, Exit.

Gate cell values on Email rows:
- `MKT`: action condition `SEG_CAN_RECEIVE_MARKETING` and not
  `SEG_FREQUENCY_CAP_REACHED`, plus the L4 pre-send webhook and branch.
- `BONUS`: `MKT` plus action condition `SEG_CAN_RECEIVE_BONUS` and the bonus
  sub-limit; the L4 request carries `"is_bonus": true`.
- `TXN`: action condition `SEG_CAN_RECEIVE_TRANSACTIONAL`.
Non-Email rows take `-`. Every Email row in a MKT or VIP journey has `MKT` or
`BONUS` (validator rule C07).

## Guardrail metrics
- Transactional: delivery above 99.5%, verification or KYC completion rate.
- Marketing: unsubscribe rate below 0.5-1% per send, complaint rate below
  0.05%, bonus-abuse rate, RG escalations among recipients (should not exceed
  the base rate).
- RG: response rate, limit-adoption rate, time from escalation to email.

## Compliance notes per journey
- TXN_01: no inducement before age and identity verification.
- SVC_02: service tone only; the email may say what verification unlocks, not
  promote offers.
- MKT_03-06, MKT_09-10, VIP_11 bonus emails: wagering terms, expiry and key
  conditions stated in the email.
- MKT_09, MKT_10: no loss-chasing wording, no "win back" framing.
- MKT_10: if `real_money_balance > 0`, a separate transactional balance notice
  is sent regardless of marketing status.
- VIP_11: perks suspend on any RG escalation; host contact is service-only.
- RG_12: zero promotional content, ever.
- SYS_13: AML and fraud wording approved by compliance (tipping-off rules).
- SYS_15: no offers; asks only whether to keep receiving mail.

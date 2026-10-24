# Journey flows: engagement

Context: full specs and flow tables for MKT_06 to MKT_10 and VIP_11. Read the
one you need for blueprint sections 7-8 or a FLOW journey, then adapt it.
Gate codes and the timing rule are explained in the journey catalogue reference.

## Contents
- JRN_MKT_06_Bonus_Lifecycle
- JRN_MKT_07_Cross_Sell
- JRN_MKT_08_Active_Retention
- JRN_MKT_09_Churn_Prevention
- JRN_MKT_10_Dormant_Reactivation (with timing check; MKT_04, MKT_07 and
  MKT_08 checks are in the journey catalogue)
- JRN_VIP_11_VIP_Lifecycle

## JRN_MKT_06_Bonus_Lifecycle
| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_06_Bonus_Lifecycle` |
| type | Marketing |
| trigger | `bonus_claimed` (progress path). The offer itself goes out as an API-triggered broadcast (below), because an event trigger takes one event |
| entry_conditions | `IN SEG_CAN_RECEIVE_MARKETING AND IN SEG_CAN_RECEIVE_BONUS AND rg_risk_level == "low"` and not in `SEG_DORMANT_30`, `SEG_DORMANT_60` or `SEG_DORMANT_90` (MKT_10 runs exclusive). These are steady-state attributes the claim does not change, so they have no sync lag at trigger time. The bonus service sends `identify()` with `wagering_progress_pct = 0` and `active_bonus_id` before `track("bonus_claimed")`, so a value left from an earlier bonus never releases the wait |
| exit_conditions | `bonus_completed` or `bonus_expired` for this `bonus_id` (event time after the trigger); enters `SEG_BONUS_ABUSE_SUPPRESSED`; `rg_risk_level` is not low; `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`) |
| subscription_topic | Casino Offers or Sportsbook Offers by bonus product |
| suppression_checks | L2 entry; L3 and L4 per email; every email is `BONUS` (bonus sub-limit, `bonus_abuse_flag != true`, medium risk excluded) |
| frequency_cap | Player's active segment cap (active_casual: 1/day, 2/week, 24h cooldown; active_core: 1/day, 4/week, 12h cooldown) with the weekly bonus sub-limit |
| flow_steps | Progress update when wagering reaches 50%; offer and unclaimed reminder are broadcasts |
| wait_times | Wait Until `wagering_progress_pct >= 50`, max 30 d (the operator's bonus validity; state the value) |
| branch_logic | Wait Until Conditions path (`wagering_progress_pct >= 50`) sends the update; the Max time path exits without an email |
| email_purpose | Keep the player informed of bonus progress and terms |
| personalisation_fields | `customer.first_name` (default "there"), `event.bonus_value` (default "see account"), `event.wagering_requirement` (default "see terms"), `customer.wagering_progress_pct` (default 0) |
| conversion_event | `bonus_completed` |
| guardrail_metrics | Claim rate; bonus-abuse rate; RG escalations among recipients; unsubscribe below 0.5% |
| compliance_notes | Wagering requirement, game weighting and expiry in every email; no countdown or scarcity framing; market bonus rules from `references/markets.json` in a Bonus terms table |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Wait | until `wagering_progress_pct >= 50`, max 30 d | - | - | - | - | - | `bonus_completed`, `bonus_expired` |
| 2 | Branch | - | Conditions path (progress 50%+) | - | - | Max time path exits | - | max time: exit |
| 3 | Email | 0 | progress 50%+ | BONUS | Progress update | Bonus progress, remaining terms, safer-play tools | first_name, wagering_progress_pct | - |
| 4 | Exit | - | - | - | - | - | - | `bonus_completed` or `bonus_expired` |

Offer path (broadcast, same templates): an API-triggered broadcast to
`SEG_CAN_RECEIVE_BONUS` minus the dormant segments, with the marketing action
conditions, `LIM_EMAIL_MKT_STD` (daily and weekly rules), and Gate
`BONUS` on the offer email (value, terms, expiry date). One factual reminder
broadcast 48h later goes only to recipients without `active_bonus_id`; the
bonus service fires `bonus_offer_expired` when the claim window closes.

## JRN_MKT_07_Cross_Sell
| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_07_Cross_Sell` |
| type | Marketing |
| trigger | Person enters `SEG_CROSS_SELL_ELIGIBLE` (either direction) |
| entry_conditions | `IN SEG_CAN_RECEIVE_MARKETING AND IN SEG_CROSS_SELL_ELIGIBLE` |
| exit_conditions | Leaves `SEG_CROSS_SELL_ELIGIBLE` (configured as the segment-leave event: a wager in the other vertical moves the player out of `SEG_CASINO_ONLY` or `SEG_SPORTSBOOK_ONLY` at the next batch, and inactivity over 30 days also leaves it); 7 d elapsed; `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`). No event exits: journey-wide exits cannot depend on direction, and a wager in the player's own vertical must not end the journey |
| subscription_topic | Topic of the target vertical (Sportsbook Offers or Casino Offers) |
| suppression_checks | L2 entry; L3 and L4 per email; `cross_sell_cap_reached != true`; offer email `BONUS`; UK: each email also needs the target product's consent attribute (`consent_betting_email` for casino to sports, `consent_casino_email` for sports to casino) and the offer is single-product |
| frequency_cap | active_core: 1/day, 4/week, 12h cooldown, 2 cross-sell/week |
| flow_steps | Introduction to the other vertical; intro offer for bonus-eligible players |
| wait_times | 0, 96h |
| branch_logic | Direction by `IN SEG_CROSS_SELL_CASINO_TO_SPORTS` (else sports to casino); before the offer, `IN SEG_CROSS_SELL_ELIGIBLE AND IN SEG_CAN_RECEIVE_BONUS` |
| email_purpose | Introduce the other product to an active single-vertical player |
| personalisation_fields | `customer.first_name` (default "there"), `customer.preferred_sport` (default "football"), `customer.preferred_casino_category` (default "slots") |
| conversion_event | `bet_placed` (casino to sports); `first_game_played` (sports to casino) |
| guardrail_metrics | Cross-sell conversion; RG escalations among converters; unsubscribe below 0.5% |
| compliance_notes | No encouragement to increase overall play; offer terms stated |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Branch | - | `IN SEG_CROSS_SELL_CASINO_TO_SPORTS` | - | - | Direction | - | - |
| 2 | Email | 0 | casino to sports | MKT | Introduction to the sportsbook | How betting works, featured markets | first_name, preferred_sport | - |
| 3 | Email | 0 | sports to casino | MKT | Introduction to the casino | Game categories, RTP information | first_name, preferred_casino_category | - |
| 4 | Wait | 96h | - | - | - | - | - | leaves `SEG_CROSS_SELL_ELIGIBLE` |
| 5 | Email | 0 | `IN SEG_CROSS_SELL_ELIGIBLE AND IN SEG_CAN_RECEIVE_BONUS`; direction picks first-bet or free spins | BONUS | Intro offer, clear terms | First-bet or free spins offer with terms | first_name | - |
| 6 | Exit | - | - | - | - | - | - | leaves the segment, or 7 d |

## JRN_MKT_08_Active_Retention
| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_08_Active_Retention` |
| type | Marketing |
| trigger | Recurring schedule every 14 days (Tuesday 10:00 in the player's zone) for `SEG_ACTIVE_CASUAL` and `SEG_ACTIVE_CORE`; one active instance per person, so a run ends before the next one starts |
| entry_conditions | `IN SEG_CAN_RECEIVE_MARKETING AND (IN SEG_ACTIVE_CASUAL OR IN SEG_ACTIVE_CORE) AND days_since_last_play <= 10 AND vip_status == "standard"` (the 10-day bound keeps entry inside the exit window and keeps MKT_08 emails out of MKT_09's first cap window, which starts on day 14 with `SEG_CHURN_RISK`; timing check in the catalogue) |
| exit_conditions | `days_since_last_play > 14`; enters `SEG_CHURN_RISK` (hand-off to MKT_09); `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`) |
| subscription_topic | Casino Offers or Sportsbook Offers by `preferred_product` |
| suppression_checks | L2 entry; L3 and L4 per email |
| frequency_cap | active_casual: 1/day, 2/week, 24h cooldown; active_core: 1/day, 4/week, 12h cooldown |
| flow_steps | Content email in week 1; loyalty progress email in week 2; run ends after 13 days |
| wait_times | 0, 7 d, 6 d |
| branch_logic | `preferred_product` content; step 3 sends only while `days_since_last_play <= 10`; `vip_progress_pct >= 75` adds a tier progress block |
| email_purpose | Keep active players informed: new games, fixtures, loyalty progress |
| personalisation_fields | `customer.first_name` (default "there"), `customer.vip_tier` (default "none"), `customer.vip_progress_pct` (default 0) |
| conversion_event | `deposit_successful`; `game_played`; `bet_placed` |
| guardrail_metrics | WAU/MAU; CTOR; unsubscribe below 0.5% per send |
| compliance_notes | Content-led; any offer belongs in MKT_06 |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Email | 0 | `preferred_product` variant | MKT | What is new this week | New games or key fixtures | first_name, preferred_product | - |
| 2 | Wait | 7 d | - | - | - | - | - | inactivity above 14 d |
| 3 | Email | 0 | `days_since_last_play <= 10` (else skip); `vip_progress_pct >= 75` adds block | MKT | Loyalty progress | Tier progress, safer-play reminder | first_name, vip_tier, vip_progress_pct | - |
| 4 | Wait | 6 d | - | - | - | - | - | inactivity above 14 d |
| 5 | Exit | - | - | - | - | - | - | run complete; next scheduled run re-enters |

## JRN_MKT_09_Churn_Prevention
| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_09_Churn_Prevention` |
| type | Marketing |
| trigger | Person enters `SEG_CHURN_RISK` (day 14 since last wager; segment trigger). Activation: only future additions |
| entry_conditions | `IN SEG_CAN_RECEIVE_MARKETING AND IN SEG_CHURN_RISK` |
| exit_conditions | Any wager after the trigger: `bet_placed` or `game_played` with event time after the trigger event; `deposit_successful` after the trigger; `days_since_last_bet < 14` (left the segment); enters `SEG_DORMANT_30` (hand-off to MKT_10); `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`) |
| subscription_topic | Casino Offers; Sportsbook Offers when `preferred_product == "sportsbook"` |
| suppression_checks | L2 entry; L3 and L4 per email; offer email adds `SEG_CAN_RECEIVE_BONUS` |
| frequency_cap | churn_risk: 1/day, 2/week, 24h cooldown, 1 bonus/week (journey emails 4 days apart, so a rolling 7-day window never holds more than two of them) |
| flow_steps | What is new (day 14); personal picks (day 18); offer for bonus-eligible players (day 22) |
| wait_times | 0, 4 d, 4 d |
| branch_logic | `IN SEG_CAN_RECEIVE_BONUS` for the offer; `preferred_product` for content and topic. Returners leave through the exits, so no activity branch is needed |
| email_purpose | Re-engage before dormancy with relevance, not pressure |
| personalisation_fields | `customer.first_name` (default "there"), `customer.preferred_product` (default casino content), `customer.preferred_casino_category` (default "slots") |
| conversion_event | `deposit_successful`; `bet_placed`; `game_played` |
| guardrail_metrics | Win-back rate; unsubscribe below 1%; RG escalations among recipients |
| compliance_notes | No loss references or "win back" framing; offer terms stated |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Email | 0 | - | MKT | Relevance: what is new | New titles or fixtures by preference | first_name, preferred_product | - |
| 2 | Wait | 4 d | - | - | - | - | - | any wager |
| 3 | Email | 0 | - | MKT | Personal picks | Picks from preferred category | first_name, preferred_casino_category | - |
| 4 | Wait | 4 d | - | - | - | - | - | any wager |
| 5 | Branch | - | `IN SEG_CAN_RECEIVE_BONUS` | - | - | Offer for eligible players; others exit | - | not eligible: exit |
| 6 | Email | 0 | bonus-eligible | BONUS | Plain offer statement | Modest reload with full terms | first_name | - |
| 7 | Exit | - | - | - | - | - | - | conversion or enters `SEG_DORMANT_30` |

Timing check: emails on days 14, 18 and 22 since the last wager. At day 22
the rolling 7-day window (days 15-22) holds only the day-18 email, so the
churn_risk weekly cap of 2 leaves room for the offer; each email clears the
24h cooldown, and day 22 is still inside `SEG_CHURN_RISK` (14-29 days).

## JRN_MKT_10_Dormant_Reactivation
| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_10_Dormant_Reactivation` |
| type | Marketing |
| trigger | Person enters `SEG_DORMANT_REACHABLE` (`IN SEG_DORMANT_ANY AND IN SEG_CAN_RECEIVE_MARKETING`). The trigger must be this combined segment, not `SEG_DORMANT_ANY` alone: a player who becomes dormant while ineligible (for example unverified or unconsented) and becomes marketing-eligible later, say at day 45 or 60, enters the combined segment at that moment and is picked up, starting at their tier branch. A trigger on `SEG_DORMANT_ANY` alone would fire once at day 30, fail the entry filter, and never fire again for that episode. Campaign setting: one active instance per person; moving from 30 to 60 days does not re-trigger, and re-entry needs the player to leave and re-enter the combined segment. Activation: only future additions. A launch backfill of players already in `SEG_DORMANT_REACHABLE` is an explicit operator decision, run once as a separate reviewed broadcast through the same gate with caps applied |
| entry_conditions | `IN SEG_DORMANT_REACHABLE` (equivalently `IN SEG_CAN_RECEIVE_MARKETING AND IN SEG_DORMANT_ANY`) |
| exit_conditions | Any wager after the trigger: `bet_placed` or `game_played` with event time after the trigger; `deposit_successful` after the trigger; leaves `SEG_DORMANT_ANY` (back under 30 days, or reaching day 90, where SYS_15 owns the "keep hearing from us" email); `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`) |
| subscription_topic | Casino Offers; Sportsbook Offers when `preferred_product == "sportsbook"` |
| suppression_checks | L2 entry; L3 and L4 per email; the offer email needs `SEG_REACTIVATION_ELIGIBLE` (includes `SEG_CAN_RECEIVE_BONUS`) and `bonus_cap_reached != true` |
| frequency_cap | dormant_30: 1/day, 1/week, 48h cooldown; dormant_60: 1/day, 1/week, 336h cooldown, 1 bonus/week |
| flow_steps | Tier branch at entry; 30-day tier: what has changed; 60-day tier: offer for eligible players, content-only update otherwise; at day 90 the player leaves `SEG_DORMANT_ANY` and the journey ends (SYS_15 owns day 90) |
| wait_times | 0; wait until `IN SEG_DORMANT_60` (max 35 d); wait until the player leaves `SEG_DORMANT_ANY` (max 35 d) |
| branch_logic | Tier at entry (`IN SEG_DORMANT_60`, otherwise 30); `IN SEG_REACTIVATION_ELIGIBLE` for the offer; `preferred_product` for content and topic; `real_money_balance > 0` sends a separate transactional balance notice outside this journey |
| email_purpose | Reactivate lapsed players with updates and, where eligible, one modest offer with full terms |
| personalisation_fields | `customer.first_name` (default "there"), `customer.preferred_product` (default casino content), `customer.currency` (default "EUR") |
| conversion_event | `deposit_successful` |
| guardrail_metrics | Reactivation rate within 14 d; bounce and complaint rates; RG escalations among reactivated players, including `sudden_activity_after_dormancy` |
| compliance_notes | No loss-chasing; offer states wagering terms and expiry; the balance notice is transactional and independent of marketing status |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Branch | - | `IN SEG_DORMANT_60` to step 4; `days_since_last_bet >= 46` (late 30-day entrant) to step 3; otherwise step 2 | - | - | Route each entrant to its tier; a late entrant skips the 30-day email so the day-60 email is not lost to the 336h cooldown | - | - |
| 2 | Email | 0 | 30-day tier | MKT | What has changed | Product updates, new features | first_name, preferred_product | - |
| 3 | Wait | until `IN SEG_DORMANT_60`, max 35 d | - | - | - | - | - | any wager, left dormancy |
| 4 | Branch | - | `IN SEG_REACTIVATION_ELIGIBLE` | - | - | Offer vs content-only update | - | - |
| 5 | Email | 0 | eligible | BONUS | Return offer, plain terms | Reactivation bonus with wagering terms and expiry | first_name, currency | - |
| 6 | Email | 0 | not eligible | MKT | Highlights | Content-only update | first_name, preferred_product | - |
| 7 | Wait | until not `IN SEG_DORMANT_ANY`, max 35 d | - | - | - | - | - | any wager, leaves `SEG_DORMANT_ANY` |
| 8 | Exit | - | - | - | - | - | - | leaves `SEG_DORMANT_ANY`; at day 90 SYS_15 takes over |

Timing check (each step's condition holds when the player reaches it):
- Enters between day 46 and day 59 (became marketing-eligible late): step 1
  skips the 30-day email and waits at step 3; the day-60 email is then the
  first in 14 days, so the dormant_60 336h cooldown cannot skip it.
- Enters at day 30: step 2 at day 30; step 3 releases at day 60, so step 4
  sees `IN SEG_DORMANT_60` and every player gets step 5 or step 6 (day 60);
  at day 90 the player leaves `SEG_DORMANT_ANY` and exits.
- Enters at day 60 (first marketing-eligible at 60): step 1 sends them to
  step 4 at day 60, then the same path.
- Already dormant on launch day: with "only future additions" this player is
  not mailed by MKT_10 in this episode unless the operator approves the
  reviewed launch broadcast; the next episode enters normally.
- A wager or deposit before the trigger never exits a player at entry: event
  exits count only events with a time after the trigger event.
- Day 90 and later: not in `SEG_DORMANT_ANY`, so MKT_10 never sends; SYS_15
  sends the single "keep hearing from us" email to players also in
  `SEG_EMAIL_UNENGAGED`. One journey owns that message.
- The two MKT_10 emails are about 30 days apart, well clear of the 48h and
  336h cooldowns, and MKT_10 no longer sends at day 90, so the 720h
  dormant_90 cooldown can never skip one of its emails.
- The `max 35 d` limit only matters if the daily batch that updates
  `days_since_last_bet` stalls.
- Steps 3 and 7 are Customer.io Wait Until blocks: a Conditions path plus a
  Max time path (35 d).

## JRN_VIP_11_VIP_Lifecycle
| Dimension | Specification |
|---|---|
| journey_id | `JRN_VIP_11_VIP_Lifecycle` |
| type | VIP marketing |
| trigger | `vip_status_changed` (the loyalty service sends it on qualification too; the qualification event is a conversion event here, not a trigger) |
| entry_conditions | Keyed on the payload, because `vip_status` and `vip_tier` sync 15 minutes after the event: `event.direction IN ["up","host_assigned"] AND event.new_tier != "none"`, plus `IN SEG_CAN_RECEIVE_MARKETING AND rg_risk_level == "low"` (steady-state, not changed by the trigger). A downgrade never enters; a host-managed promotion without the GGR threshold does |
| exit_conditions | tier downgrade (a later `vip_status_changed` with `direction == "down"`, after the trigger); `rg_risk_level != "low"`; `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`) |
| subscription_topic | VIP & Loyalty |
| suppression_checks | L2 entry; L3 and L4 per email; perk emails `BONUS`; VIP status never overrides suppression |
| frequency_cap | vip/high_roller: 1/day, 5/week, 8h cooldown, 3 bonus/week |
| flow_steps | Tier welcome and benefits; host introduction for gold-plus or host-managed players; tier perk at day 14; tier review at day 44, then the journey ends and re-enters on the next tier change |
| wait_times | 0, 14 d, 30 d |
| branch_logic | `event.new_tier` (gold and above get host introduction); `event.direction == "host_assigned"` routes to the host webhook; attributes are read only from step 4 on, after the 14-day wait |
| email_purpose | Recognise the tier, explain benefits and the host relationship |
| personalisation_fields | `customer.first_name` (default "there"), `event.new_tier` (default "your new tier") in the day-0 email, `customer.vip_tier` (default "none") later, `customer.vip_progress_pct` (default 0) |
| conversion_event | `deposit_successful` within 30 d of tier change |
| guardrail_metrics | VIP retention; RG escalations among VIPs; complaint rate |
| compliance_notes | RG escalation exits the journey and notifies the host within 15 minutes; perks require completed KYC and enhanced due diligence where applicable |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Email | 0 | - | MKT | Tier recognition | Tier benefits, how tiers work | first_name, new_tier | - |
| 2 | Branch | - | `event.new_tier IN ["gold","platinum","diamond"] OR event.direction == "host_assigned"` | - | - | Host path | new_tier | - |
| 3 | Webhook | 0 | host path | - | - | Assign host, notify host tooling | user_id, new_tier | - |
| 4 | Wait | 14 d | - | - | - | - | - | downgrade or RG change |
| 5 | Email | 0 | `IN SEG_CAN_RECEIVE_BONUS` | BONUS | Tier perk, plain terms | Perk with terms | first_name, vip_tier | - |
| 6 | Wait | 30 d | - | - | - | - | - | downgrade or RG change |
| 7 | Email | 0 | - | MKT | Tier review | Progress, limits and safer-play tools | first_name, vip_progress_pct | - |
| 8 | Exit | - | - | - | - | - | - | downgrade, RG escalation, or re-entry on next tier change |

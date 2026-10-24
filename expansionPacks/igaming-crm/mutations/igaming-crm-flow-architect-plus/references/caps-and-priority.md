# Frequency caps, priority and conflict rules

Context: the per-segment cap table, how caps are evaluated and counted, the
11-level journey priority order and the conflict matrix. Read it for blueprint
sections 11-12, any FLOW caps piece, and the cap part of every journey spec.

## Contents
- Key idea
- Cap table
- Evaluation order
- Most restrictive cap wins
- Counter mechanics
- Customer.io implementation
- 11-level priority order
- Conflict matrix
- Pause versus exit

## Key idea
Caps limit Layer-3 marketing only. RG, transactional and system messages never
count toward a cap and are never blocked by one. Zero-cap rows are suppression
expressed as caps; the gate blocks those players first.

## Cap table
Cooldown is hours since `last_marketing_email_sent_at`.

| Segment key | Daily | Weekly | Cooldown (h) | Bonus per week | Cross-sell per week | CIO frequency cap (rest backend) |
|---|---|---|---|---|---|---|
| new_registrant | 1 | 3 | 24 | 2 | 1 | LIM_EMAIL_MKT_STD |
| no_deposit | 1 | 3 | 24 | 2 | 1 | LIM_EMAIL_MKT_STD |
| first_depositor | 1 | 4 | 24 | 1 | 1 | LIM_EMAIL_MKT_STD |
| active_casual | 1 | 2 | 24 | 1 | 1 | LIM_EMAIL_MKT_STD |
| active_core | 1 | 4 | 12 | 2 | 2 | LIM_EMAIL_MKT_STD |
| vip / high_roller | 1 | 5 | 8 | 3 | 2 | LIM_EMAIL_MKT_VIP |
| churn_risk | 1 | 2 | 24 | 1 | 1 | LIM_EMAIL_MKT_STD |
| dormant_30 | 1 | 1 | 48 | 1 | 0 | LIM_EMAIL_MKT_STD |
| dormant_60 | 1 | 1 | 336 | 1 | 0 | LIM_EMAIL_MKT_STD |
| dormant_90 | 1 | 1 | 720 | 1 | 0 | LIM_EMAIL_MKT_STD |
| kyc_pending / unverified_email | 1 | 2 | 24 | 0 | 0 | LIM_EMAIL_MKT_STD |
| sms_opted_in (SMS channel) | 1 | 2 | 24 | 1 | 1 | LIM_SMS_MKT_WEEKLY |
| rg_medium | 1 | 1 | 48 | 0 | 0 | LIM_EMAIL_MKT_STD |
| rg_high, rg_severe, timeout, self_excluded, aml_restricted, global_suppressed | 0 | 0 | n/a | 0 | 0 | none (gate blocks) |
| bonus_abuse (bonus mail only) | 1 | 2 | 24 | 0 | 0 | LIM_EMAIL_MKT_STD |

The CIO frequency cap column names the Customer.io frequency cap that carries
the platform part of each row; every value tighter than those caps (the
per-segment weekly counts, cooldowns, bonus and cross-sell sub-limits) stays in the backend
flags (Customer.io implementation, below).

Segment keys map to segments: new_registrant `SEG_NEW_REGISTRANT`, no_deposit
`SEG_NO_DEPOSIT_ELIGIBLE`, first_depositor `SEG_FIRST_DEPOSITOR`, active_casual
`SEG_ACTIVE_CASUAL`, active_core `SEG_ACTIVE_CORE`, vip/high_roller
`vip_status == "vip"` or `SEG_HIGH_ROLLER`, churn_risk `SEG_CHURN_RISK`,
dormant_* `SEG_DORMANT_*`, kyc_pending `SEG_KYC_INCOMPLETE`, rg_medium
`SEG_RG_MEDIUM`, the zero row `SEG_RG_SUPPRESSED`, `SEG_AML_RESTRICTED`,
`SEG_UNSUBSCRIBED`, bonus_abuse `SEG_BONUS_ABUSE_SUPPRESSED`.

Dormant cooldowns of 336 h (14 days) and 720 h (30 days) cap all marketing to
60- and 90-day dormant players (broadcasts and any other journey included) at
one email per fortnight and one per month. MKT_10 sends at day 30 and day 60
only (about 720 h apart, against a 336 h cooldown at day 60) and leaves the
ladder at day 90, so no MKT_10 email can collide with the 720 h dormant_90
cooldown. From day 90 the only planned email is SYS_15's transactional
keep-in-touch message, which is cap-exempt. Shorter cooldowns from older
drafts are not used.

Cap notation: in journey specs, `segment: N/day, N/week, Nh cooldown[, N
bonus/week]`; in the catalogue table, `segment daily/weekly` (for example
`churn_risk 1/2`).

## Evaluation order
1. Gate (all fourteen conditions plus topic).
2. Zero-cap segment: block.
3. Cooldown since `last_marketing_email_sent_at`.
4. Daily count `marketing_emails_sent_today`.
5. Weekly count `marketing_emails_sent_last_7d`.
6. Sub-limit: `bonus_emails_sent_last_7d` for bonus mail,
   `cross_sell_emails_sent_last_7d` for cross-sell mail.

## Most restrictive cap wins
A player in several cap segments gets, per column, the smallest daily, weekly,
bonus and cross-sell value and the largest cooldown across those segments.
Example: active_core and rg_medium together give daily 1, weekly 1, cooldown
48 h, bonus 0, cross-sell 0.

## Counter mechanics
- The backend counter service increments the counters from the Customer.io
  delivered webhook for Layer-3 messages only, within 1 hour.
- `marketing_emails_sent_today` counts a rolling 24h window and the 7-day
  counters a rolling 7-day window, recomputed from the send log, matching the
  relative windows of the Customer.io limits. The counter service still runs
  for the person-level layer below.
- After each update the service evaluates the effective caps and writes
  `frequency_cap_reached`, `bonus_cap_reached` and `cross_sell_cap_reached`.
- The L4 pre-send check re-evaluates caps live, so a burst inside the 1-hour
  counter SLA is still blocked.

## Customer.io implementation
Two layers.

1. Frequency caps (named caps, the app's "Message frequency limits" page
   in Workspace Settings), referenced per
   automation or message. A cap is a name plus rules; each rule limits a set of
   channels to `cap_limit` messages per rolling `window_secs`. An automation
   references one cap, so a class's daily and weekly allowances are two rules
   in one cap (one cap holding two email rules: verify in workspace). Opting in
   is explicit: a message that does not use limits counts toward nothing.
   | Cap | Rules | Assigned to |
   |---|---|---|
   | `LIM_EMAIL_MKT_STD` | email 1 per 1 day; email 4 per 7 days | every MKT automation and promotional broadcast |
   | `LIM_EMAIL_MKT_VIP` | email 1 per 1 day; email 5 per 7 days | VIP_11 |
   | `LIM_SMS_MKT_WEEKLY` | SMS 2 per 7 days | every marketing SMS step |
   Windows are relative, not calendar days: a slot reopens one full window
   after the oldest counted message. The older single workspace message limit
   is deprecated and is never set; where a workspace still has one, it shows
   as a cap named `Default`. RG, TXN, SVC and SYS automations never use limits,
   and an RG or service message inside a mixed workflow is set not to count
   towards any limit. Retry window (`retry_window_secs`): at most 24h for
   marketing (a longer retry sends stale content), none for time-bound offers.
   A message with no slot before its retry window ends is marked Undeliverable
   and the person continues, so timing walks assume a capped email may be
   skipped. Per-automation rate limits are a different setting (send speed,
   below).
2. Person-level caps the platform cannot express (limits attach to
   automations, not to a player's segment): the per-segment rows, cooldowns,
   bonus and cross-sell sub-limits stay as backend flags in action conditions.
   Segment conditions cannot compare two attributes, so they are evaluated in
   the backend and exposed as flags:
```text
SEG_FREQUENCY_CAP_REACHED := frequency_cap_reached == true
Email action condition (marketing): IN SEG_CAN_RECEIVE_MARKETING
                                    AND NOT IN SEG_FREQUENCY_CAP_REACHED
Email action condition (bonus):     add IN SEG_CAN_RECEIVE_BONUS AND bonus_cap_reached != true
Email action condition (cross-sell): add cross_sell_cap_reached != true
```
Broadcasts use the same filters in their audience definition. Per-automation
rate limits (1 to 60,000 messages per minute per channel, automations only)
control send speed for reactivation waves; they are never a cap, because they
limit how fast the automation sends, not how often one player receives. A
message over the rate waits in the queue while the person moves on to the
next action, so a later step on a faster channel can arrive first, and a
frequency cap is checked only when the queued message finally sends.

## 11-level priority order
| Level | Category | Journeys |
|---|---|---|
| 1 | RG and self-exclusion | RG_12 (with SE and timeout confirmations) |
| 2 | Account security, compliance and preference confirmations | SYS_13, SVC_02, SYS_14 |
| 3 | Financial and transactional | TXN_01, deposit and withdrawal receipts |
| 4 | Churn prevention | MKT_09 |
| 5 | VIP | VIP_11 |
| 6 | Activation | MKT_04, MKT_03 |
| 7 | Cross-sell | MKT_07 |
| 8 | Active retention | MKT_08, MKT_05 |
| 9 | Promotional bonus | MKT_06 |
| 10 | Dormant reactivation | MKT_10 |
| 11 | List hygiene | SYS_15 |

Change from the source order: preference confirmations (SYS_14) moved from
level 11 into level 2, because confirming an unsubscribe is a compliance
obligation, not maintenance. Levels 1-3 are never capped; levels 4-10 share
the cap. Customer.io documents no priority between messages competing for a
limit: whichever message is attempted first takes the slot, and an email that
reaches a full backend cap fails its action condition (`NOT IN
SEG_FREQUENCY_CAP_REACHED`) and is skipped. The 11-level order is a design
convention enforced by cap budgets, timing and upstream orchestration: cap
budgets sized for the journeys that overlap
(first_depositor weekly 4 = MKT_04's three emails plus one MKT_05 email), the
conflict matrix below, and timing that keeps overlapping journeys out of the
same cooldown window. Level 11 is non-marketing and cap-exempt.

## Conflict matrix
| Pair | Rule | Implementation |
|---|---|---|
| RG_12 vs any MKT or VIP | Immediate exit and suppression until a review clears | `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`) plus `rg_risk_level != "low"` exit on bonus and VIP journeys |
| SYS_13 or SVC_02 vs promotional journeys | Pause 24 h, then re-check | Wait-and-recheck branch on `security_flag_active != true` and `kyc_status` |
| VIP_11 vs MKT_08 or MKT_07 | VIP subsumes standard retention | MKT_08 entry requires `vip_status == "standard"`; MKT_07 holds 72 h after a VIP_11 email |
| MKT_04 vs MKT_03 | Exit MKT_03 | MKT_03 exit on `deposit_successful` |
| MKT_07 vs MKT_08 | Interleave with 72 h spacing; cross-sell queues behind retention | Cooldown plus a 72 h wait before cross-sell emails when MKT_08 sent recently |
| MKT_09 vs MKT_08 | Exit MKT_08 into MKT_09 | MKT_08 exit on entering `SEG_CHURN_RISK` |
| MKT_10 vs MKT_06 | Dormant runs exclusive; bonus broadcasts held | MKT_06 entry excludes `SEG_DORMANT_30`, `SEG_DORMANT_60`, `SEG_DORMANT_90` |

## Pause versus exit
- Exit: safety and lifecycle supersession, configured as journey exit
  conditions (segment entry or attribute change). Use for RG, SE, timeout, AML,
  unsubscribe, conversion and hand-offs.
- Pause: a wait step followed by a branch that re-checks a segment or attribute
  (for example `security_flag_active != true`) and loops at most a fixed number
  of times before exiting. Use for temporary holds such as a security review.
- Do not implement either with Liquid in the email body: Liquid controls
  content, not whether a journey sends.

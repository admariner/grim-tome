# Responsible gambling automation

Context: RG signals, actions per risk level, bonus suppression, VIP rules, the
RG intervention logic and the monthly spending summary. Read it for blueprint
section 10, any FLOW rg piece, and the RG part of every audit. Helplines and
registers per market live in the compliance-and-overlays reference.

## Contents
- Key idea
- Risk signals
- Actions by risk level
- Bonus suppression by risk level
- VIP and high-value rules
- RG_12 intervention logic
- Timeout and self-exclusion handling
- Monthly spending summary
- Minimum standards

## Key idea
The RG layer is built and tested before any marketing journey goes live. RG
messages use `SEG_CAN_RECEIVE_TRANSACTIONAL`, are never suppressed by the
marketing gate, never carry offers, and are exempt from caps. VIP status, high
GGR and loyalty tier never override RG suppression.

## Risk signals
The RG model (backend) evaluates signals and writes `rg_risk_level`; it also
sends `rg_signal_detected` and, on an increase, `rg_risk_escalated`, each with
the normalised `rg_intervention_required` that triggers RG_12. Signals that
compare a player to their own baseline (`deposit_velocity_spike`,
`loss_velocity_spike`) are computed by the RG model and written as a boolean
or enum; no segment compares `ggr_last_7d` with `ggr_last_30d`, because
segments cannot compare two attributes.

| Signal (`signal_type`) | Source | Threshold | Pushes toward |
|---|---|---|---|
| `deposit_velocity_spike` | `deposits_last_7d` | 4+ deposits in 7 days, above personal baseline | medium |
| `failed_deposits_3x_24h` | `deposit_failed` count | 3+ failed deposits in 24 h | medium |
| `session_duration_threshold_hit` | `session_duration_avg_mins` | single session 180+ min or average 120+ min | medium |
| `loss_velocity_spike` | `ggr_last_7d` | 7-day loss above 3x the personal 30-day average | medium to high |
| `overnight_play_pattern` | `game_played` timestamps | play 01:00-05:00 local on 3+ consecutive nights | medium |
| `limit_removed` | `limit_removed` event | any limit removed or increased | medium |
| `rg_page_visited` | `responsible_gambling_page_visited` | any visit | low (monitoring) |
| `sudden_activity_after_dormancy` | `days_since_last_bet`, `deposits_last_7d` | return after 30+ dormant days with 3+ deposits in week 1 | medium |
| `multiple_bonus_claims_with_high_losses` | `bonus_claimed` count, `ggr_last_30d` | 3+ bonuses with net loss above 5x average deposit | medium to high |
| `limit_breach_attempt` (optional) | limit service | attempt to exceed a self-set limit, or reversing a pending withdrawal | high to severe |
| `reality_checks_dismissed` (optional) | `rg_reality_check_acknowledged` | 3 consecutive dismissals | medium |
| `help_seeking` (optional) | support tooling | explicit request for help or a timeout | severe |

## Actions by risk level
| Level | Marketing | Protective action | SLA |
|---|---|---|---|
| low | Normal lifecycle marketing; standard RG footer | none | n/a |
| medium | Max 1 promotional email per week (cap row rg_medium); no bonuses; no loss-chasing or urgency offers; helpline in every email | Safer-play tools email; spending summary in the next email; escalation logged for audit | email within 24 h |
| high | All promotional email suppressed immediately | Protective email with limit-setting CTA and support resources; SE information and helpline; VIP host notified (no promotion); account review | email within 2 h |
| severe | All marketing suppressed; resuming needs manual review, a downgrade and compliance approval | Route to RG/compliance team; protective email with SE information | email within 2 h; team task immediately |
| timeout | None for the duration | Confirmation (transactional); service check 48 h before expiry; on expiry a service email; marketing does not auto-resume | confirmation immediately |
| self-excluded | Permanent for the exclusion period plus any cooling-off | Confirmation (transactional) with support services; no win-back ever | confirmation immediately; suppression within 5 min |

## Bonus suppression by risk level
| Level | Bonus offers | Free spins | Reload offers | Loyalty points |
|---|---|---|---|---|
| low | eligible | eligible | eligible | eligible |
| medium | suppressed | suppressed | suppressed | eligible |
| high | suppressed | suppressed | suppressed | suppressed |
| severe | suppressed | suppressed | suppressed | suppressed |
| timeout | suppressed | suppressed | suppressed | suppressed |
| self-excluded | suppressed | suppressed | suppressed | suppressed |

## VIP and high-value rules
1. On any escalation of a VIP's `rg_risk_level` to medium or above, the VIP's
   automated marketing journeys stop (VIP_11 exits on `rg_risk_level != "low"`).
2. The VIP host is notified within 15 minutes (webhook to the host tooling).
3. The host sends no promotional contact while suppression is active; service
   contact (account updates, withdrawal confirmations) is allowed.
4. Any exception requires written compliance approval, recorded in the audit log.

## RG_12 intervention logic
Trigger: the normalised `rg_intervention_required` event, which the backend
sends for `rg_risk_escalated`, `rg_signal_detected` with a medium-or-higher
level, `limit_removed`, `rg_loss_limit_triggered`, `rg_session_limit_reached`,
`timeout_started` and `self_exclusion_started` (fields `reason`, `risk_level`).
Entry and the first branches read the payload, never the attributes, because
`self_excluded` and `timeout_active` sync within 5 minutes and `rg_risk_level`
within 15 while the event is real time: `event.reason IN
["timeout_started","self_exclusion_started","limit_removed","loss_limit","session_limit"]
OR event.risk_level IN ["medium","high","severe"]`. A low-risk player hitting a
limit gets a factual limit notice (a branch that exits after one email), and a
self-exclusion confirmation never waits for the attribute sync.
`rg_risk_level` is read only at the 7-day review.
Gate: `SEG_CAN_RECEIVE_TRANSACTIONAL`. Topic: Safer Gambling. Cap: Exempt.
Branches:
- medium: safer-play tools email (deposit limits, reality checks, self-assessment,
  helpline) within 24 h; wait 7 d; if still medium, a second check-in; if
  escalated, follow the high branch; if reviewed down to low, exit.
- high or severe: webhook to the RG case queue (and VIP host if `vip_status !=
  "standard"`); protective email within 2 h (limits, timeout, self-exclusion,
  helpline); optional 24 h cooling-off offered as a player choice; wait 7 d;
  exit only after a recorded review sets `rg_risk_level` to low.
- timeout or self-excluded: confirmation email only, then exit; suppression
  persists through the segment flags.
Conversion: `limit_set`, `timeout_started` or `self_exclusion_started`. The full
spec and flow table are in the protective journeys reference.

## Timeout and self-exclusion handling
- Timeout expiry is a service email ("your break has ended, your limits are
  ...") with no offer. Marketing resumes only when the player is back in
  `SEG_CAN_RECEIVE_MARKETING` and a 7-day post-timeout hold has passed; the
  hold is enforced with `excluded_until < 7 days ago` on re-entry.
- Self-exclusion: the confirmation is the last message besides legally
  required service notices. Never a win-back, never a "we miss you". The
  exclusion is recorded on the profile (`self_excluded`,
  `self_exclusion_source`); the profile is never deleted or suppressed through
  the API (suppression gate reference).

## Monthly spending summary
Service message to every active player on the first working day of the month,
consent not required, no offers. Contents: deposits and withdrawals in the
period, net position (deposits minus withdrawals), time played where available,
link to set or review limits, link to safer-gambling tools and the market's
helpline. Figures come from the ledger as event or attribute data and must
match it exactly (QA check).

## Minimum standards
1. Self-exclusion suppression effective within 5 minutes.
2. Bonuses suppressed for medium risk and above.
3. Marketing frequency reduced at early risk signals (medium cap).
4. Safer-gambling message and link in every promotional email.
5. VIP status never overrides RG suppression.
6. No message encouraging a limit-setter to raise a limit.
7. No loss-chasing messages to players with recent significant losses.

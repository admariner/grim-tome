# FLOW deliverable: churn prevention journey (broken)

Validator fixture (failing case): the same journey with deliberate rule
violations, used to prove the output validator exits 1. Do not copy.

Prepared for Northwind Casino.

### JRN_MKT_09_Churn_Prevention

| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_09_Churn_Prevention` |
| type | Marketing |
| trigger | `bet_placed` or `game_played` |
| entry_conditions | `IN SEG_CHURN_RISK AND rg_risk_level == "none"` |
| exit_conditions | `bet_placed`; enters `SEG_RG_SUPPRESSED` |
| subscription_topic | Casino Offers |
| suppression_checks | Configure suppression as appropriate |
| frequency_cap | [TBD] |
| flow_steps | What is new; reload offer |
| wait_times | 0, 48h |
| branch_logic | `days_since_last_bet >= 14` |
| email_purpose | Re-engage with a reload offer |
| personalisation_fields | `customer.first_name` |
| conversion_event | `deposit_successful` |
| guardrail_metrics | Win-back rate |
| compliance_notes | No loss references |

| Step | Action | Wait | Branch condition | Subject approach | Content purpose | Exit trigger |
|---|---|---|---|---|---|---|
| 1 | Email | 0 | - | Relevance | New titles | - |
| 2 | Wait | 48h | - | - | - | `bet_placed` |
| 3 | Email | 0 | - | Offer | Reload offer | - |
| 4 | Wait | until IN SEG_DORMANT_60 | - | - | - | - |
| 4b | Wait Until `IN SEG_DORMANT_90` | - | - | - | - | - |
| 5 | Exit | - | - | - | - | conversion |

```liquid
{% if customer.days_since_last_bet >= 30 %}
  {% exit_campaign %}
  {% include 'footer' %}
Hi {{ customer.first_name }},
```

Loss-spike segment used for the offer branch:

SEG_LOSS_SPIKE := ggr_last_7d > ggr_last_30d

Offer ends in {% countdown %} hours.

Second journey: otherwise valid, but two dimensions are filled with `-` and
`n/a` (C03) and the offer email is gated MKT instead of BONUS (C09), although
the spec names the bonus segment.

### JRN_MKT_06_Bonus_Lifecycle

| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_06_Bonus_Lifecycle` |
| type | Marketing |
| trigger | Scheduled reload offer |
| entry_conditions | `IN SEG_CAN_RECEIVE_MARKETING AND IN SEG_CAN_RECEIVE_BONUS` |
| exit_conditions | `bonus_claimed`; enters `SEG_RG_SUPPRESSED` |
| subscription_topic | Casino Offers |
| suppression_checks | L2 entry; L3 and L4 per email; `SEG_CAN_RECEIVE_BONUS` |
| frequency_cap | active_casual: 1/day, 2/week, 24h cooldown, 1 bonus/week |
| flow_steps | Reload offer |
| wait_times | 0 |
| branch_logic | none needed |
| email_purpose | Present a reload offer with terms |
| personalisation_fields | `customer.first_name` (default "there") |
| conversion_event | `bonus_claimed` |
| guardrail_metrics | - |
| compliance_notes | n/a |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Email | 0 | - | MKT | Clear offer statement | Reload bonus with terms | first_name | - |
| 2 | Exit | - | - | - | - | - | - | `bonus_claimed` |

Transactional journey whose verification link has no fallback (C29: a
transactional message sends even when its Liquid fails):

### JRN_TXN_01_Email_Verification

Verify your email: {{ event.verification_url }}

## Market overlay: DE (Germany)
- Suppression and register: OASIS register match (verify before deployment).
- Disclosures: helpline BIÖG 0800 1372700; 18+ notice.
- RG requirements: safer-gambling footer on every email.

This fixture ends without the review notice on purpose.

# FLOW deliverable: welcome and reload offers (broken market rules)

Validator fixture (failing case): run with `--markets UK,SE,BR`. It must
exit 1: the Bonus terms rows break the UK 10x and single-product rules, the
SE first-play rule and the BR deposit-conditional rule (C26), the reload
journey has no Bonus terms row (C26), and the BR banner is missing (C28).
Do not copy.

### JRN_MKT_04_First_Deposit_Welcome

| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_04_First_Deposit_Welcome` |
| type | Marketing |
| trigger | `deposit_successful` where `event.deposit_number == 1` |
| entry_conditions | `IN SEG_CAN_RECEIVE_MARKETING AND event.deposit_number == 1` |
| exit_conditions | second `deposit_successful`; 7 d elapsed; `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`) |
| subscription_topic | Casino Offers |
| suppression_checks | L2 entry; L3 and L4 per email; `SEG_CAN_RECEIVE_BONUS` on the offer |
| frequency_cap | first_depositor: 1/day, 4/week, 24h cooldown, 1 bonus/week |
| flow_steps | Welcome bonus with terms |
| wait_times | 0 |
| branch_logic | `IN SEG_CAN_RECEIVE_BONUS` |
| email_purpose | Present the welcome bonus with its terms |
| personalisation_fields | `customer.first_name` (default "there") |
| conversion_event | `bonus_claimed` |
| guardrail_metrics | Bonus take-up; RG escalations among recipients |
| compliance_notes | Wagering terms in the email |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Email | 0 | bonus-eligible | BONUS | Clear offer statement | Welcome bonus with terms | first_name | - |
| 2 | Exit | - | - | - | - | - | - | 7 d |

### JRN_MKT_06_Bonus_Lifecycle

| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_06_Bonus_Lifecycle` |
| type | Marketing |
| trigger | `bonus_claimed` |
| entry_conditions | `IN SEG_CAN_RECEIVE_MARKETING AND IN SEG_CAN_RECEIVE_BONUS` |
| exit_conditions | `bonus_completed`; `bonus_expired`; `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`) |
| subscription_topic | Casino Offers |
| suppression_checks | L2 entry; L3 and L4 per email; `SEG_CAN_RECEIVE_BONUS` |
| frequency_cap | active_casual: 1/day, 2/week, 24h cooldown, 1 bonus/week |
| flow_steps | Reload offer progress |
| wait_times | 0 |
| branch_logic | `IN SEG_CAN_RECEIVE_BONUS` |
| email_purpose | Reload bonus progress and terms |
| personalisation_fields | `customer.first_name` (default "there") |
| conversion_event | `bonus_completed` |
| guardrail_metrics | Completion rate; RG escalations among recipients |
| compliance_notes | Wagering terms in the email |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Email | 0 | bonus-eligible | BONUS | Progress update | Reload bonus progress with terms | first_name | - |
| 2 | Exit | - | - | - | - | - | - | `bonus_completed` |

Bonus terms:

| Journey | Email | Market | bonus_product | wagering_multiplier | deposit_conditional | first_play_only |
|---|---|---|---|---|---|---|
| JRN_MKT_04_First_Deposit_Welcome | 1 | UK | betting+casino | 35 | no | no |
| JRN_MKT_04_First_Deposit_Welcome | 1 | SE | casino | 1 | no | no |
| JRN_MKT_04_First_Deposit_Welcome | 1 | BR | casino | 1 | yes | no |

## Market overlay: UK (United Kingdom)
- Suppression and register: GAMSTOP (verify before deployment).
- Disclosures: helpline National Gambling Helpline 0808 8020 133 (verify before deployment).
- RG requirements: safer-gambling footer.

## Market overlay: SE (Sweden)
- Suppression and register: Spelpaus (verify before deployment).
- Disclosures: helpline Stödlinjen 020-81 91 00 (verify before deployment).
- RG requirements: safer-gambling footer.

## Market overlay: BR (Brazil)
- Suppression and register: Plataforma Centralizada de Autoexclusão (verify before deployment).
- Disclosures: helpline Disque Saúde 136 / CVV 188 (verify before deployment).
- RG requirements: safer-gambling footer.

Legal/compliance review required: have qualified legal and compliance counsel review this design in every target jurisdiction before deployment.

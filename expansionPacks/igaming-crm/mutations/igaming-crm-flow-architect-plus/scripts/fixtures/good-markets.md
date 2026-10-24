MARKET STATUS: BR closed pending MP 1.394/2026 (25 Sep 2026); licences end ~25 Oct 2026. Counsel must confirm legal status before any send.

# FLOW deliverable: UK sportsbook first-deposit welcome

Validator fixture (passing case with market rules): run with
`--markets UK,BR`. It must exit 0, with the C28 warning for BR (closed
pending) and no error.

Assumptions: Customer.io; markets UK (sportsbook licence) and BR; product
sportsbook only; first_depositor cap applies.

### JRN_MKT_04_First_Deposit_Welcome

| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_04_First_Deposit_Welcome` |
| type | Marketing |
| trigger | `deposit_successful` where `event.deposit_number == 1` (activation: only future additions) |
| entry_conditions | `IN SEG_CAN_RECEIVE_MARKETING AND event.deposit_number == 1`; UK action condition `consent_betting_email == true` on every email |
| exit_conditions | second `deposit_successful` (event time after the trigger); 7 d elapsed; `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`); enters `SEG_AML_RESTRICTED` or `SEG_UNSUBSCRIBED` |
| subscription_topic | Sportsbook Offers |
| suppression_checks | L2 entry; L3 action condition and L4 pre-send webhook before every email; bonus emails add `SEG_CAN_RECEIVE_BONUS`; UK emails add `SEG_CONSENT_BETTING_EMAIL` |
| frequency_cap | first_depositor: 1/day, 4/week, 24h cooldown, 1 bonus/week |
| flow_steps | Welcome and how the free bet works (UK); content-only welcome (BR); unclaimed reminder; limits and safer-play introduction |
| wait_times | 0, 24h, 72h |
| branch_logic | `regulatory_zone == "BR"` takes the content-only path; `IN SEG_CAN_RECEIVE_BONUS` for the offer; `active_bonus_id` set or not |
| email_purpose | Confirm the start, explain the single-product welcome terms, introduce limits |
| personalisation_fields | `customer.first_name` (default "there"), `customer.active_bonus_id` (default "your welcome offer"), `customer.preferred_sport` (default "football") |
| conversion_event | `deposit_successful` with `deposit_number == 2`; `bet_placed` |
| guardrail_metrics | First-to-second deposit rate; bonus take-up; RG escalations among recipients; unsubscribe below 0.5% |
| compliance_notes | UK: wagering at most 10x, betting-only offer, opt-in per product and channel; BR: no deposit-conditional reward, content only; wagering terms in every bonus email |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Branch | - | `regulatory_zone == "BR"` | - | - | BR content-only path vs UK path | regulatory_zone | - |
| 2 | Email | 0 | BR | MKT | Welcome aboard | Getting started, limits and safer-play tools | first_name | - |
| 3 | Email | 0 | UK and `IN SEG_CAN_RECEIVE_BONUS` | BONUS | Welcome aboard | How the betting free bet works, terms | first_name, active_bonus_id | - |
| 4 | Wait | until `active_bonus_id` is set, max. 24h | - | - | - | - | - | second deposit |
| 5 | Email | 0 | UK, unclaimed | BONUS | Factual reminder | How to activate the free bet, terms | first_name | - |
| 6 | Wait | 72h | - | - | - | - | - | second deposit |
| 7 | Email | 0 | - | MKT | Getting more from your account | Deposit limits, reality checks | first_name, preferred_sport | - |
| 8 | Exit | - | - | - | - | - | - | 7 d |

Bonus terms:

| Journey | Email | Market | bonus_product | wagering_multiplier | deposit_conditional | first_play_only |
|---|---|---|---|---|---|---|
| JRN_MKT_04_First_Deposit_Welcome | 3, 5 | UK | sportsbook | 10 | yes | no |
| JRN_MKT_04_First_Deposit_Welcome | 2 | BR | none | none | no | no |

```liquid
Hi {{ customer.first_name | default: "there" }},
{% if customer.regulatory_zone == "UK" %}
  Your free bet: {{ customer.active_bonus_id | default: "your welcome offer" }}, wagering 10x, betting only.
{% endif %}
```

## Market overlay: UK (United Kingdom)
- Journey modifications: betting-only offer; every email checks `consent_betting_email == true`.
- Suppression and register: GAMSTOP match sets `self_exclusion_register_match` (verify before deployment).
- Disclosures: helpline National Gambling Helpline 0808 8020 133 (verify before deployment); licence footer; 18+.
- RG requirements: safer-gambling footer on every email.
- Bonus rules: wagering at most 10x; single product (markets.json, primary).

## Market overlay: BR (Brazil)
- Status: closed pending MP 1.394/2026; no send before counsel confirms legal status.
- Suppression and register: Plataforma Centralizada de Autoexclusão (verify before deployment).
- Disclosures: helpline Disque Saúde 136 / CVV 188 (verify before deployment); ordinance number from the `br_ordinance_number` snippet; 18+.
- RG requirements: safer-gambling footer on every email.
- Bonus rules: no deposit-conditional reward; content-only path.

Legal/compliance review required: have qualified legal and compliance counsel review this design in every target jurisdiction before deployment.

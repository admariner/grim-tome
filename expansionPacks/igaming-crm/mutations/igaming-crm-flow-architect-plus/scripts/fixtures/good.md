# FLOW deliverable: churn prevention journey

Validator fixture (passing case): a complete FLOW journey for a fictional
operator, used to prove the output validator exits 0.

Assumptions: Customer.io; market DE under an EU national licence with national
register checks; casino and sportsbook products; churn_risk cap applies.

### JRN_MKT_09_Churn_Prevention

| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_09_Churn_Prevention` |
| type | Marketing |
| trigger | Person enters `SEG_CHURN_RISK` (segment trigger; activation: only future additions) |
| entry_conditions | `IN SEG_CAN_RECEIVE_MARKETING AND IN SEG_CHURN_RISK` |
| exit_conditions | any wager (`bet_placed` or `game_played`, event time after the trigger); `deposit_successful` (after the trigger); `days_since_last_bet < 14`; enters `SEG_DORMANT_30`; `RG_EXIT_BLOCK` (includes `marketing_blocked`, `self_excluded`, `timeout_active`, `rg_risk_level` high or severe, and `SEG_RG_SUPPRESSED`); enters `SEG_AML_RESTRICTED` or `SEG_UNSUBSCRIBED` |
| subscription_topic | Casino Offers; Sportsbook Offers when preferred product is sportsbook |
| suppression_checks | L2 entry gate; L3 action condition and L4 pre-send webhook before every email; offer email adds `SEG_CAN_RECEIVE_BONUS` |
| frequency_cap | churn_risk: 1/day, 2/week, 24h cooldown, 1 bonus/week |
| flow_steps | What is new; personal picks; reload offer for bonus-eligible players |
| wait_times | 0, 48h, 72h |
| branch_logic | `IN SEG_CAN_RECEIVE_BONUS` for the offer; returners leave through the exits |
| email_purpose | Re-engage before dormancy with relevant content and one modest offer |
| personalisation_fields | `customer.first_name` (default "there"), `customer.preferred_product` (default casino content) |
| conversion_event | `deposit_successful`; `bet_placed`; `game_played` |
| guardrail_metrics | Win-back rate; unsubscribe below 1%; RG escalations among recipients |
| compliance_notes | No loss references; wagering terms and expiry in the offer email |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Email | 0 | - | MKT | Relevance: what is new | New titles or fixtures | first_name, preferred_product | - |
| 2 | Wait | 48h | - | - | - | - | - | `bet_placed` |
| 3 | Email | 0 | - | MKT | Personal picks | Picks by preference | first_name | - |
| 4 | Wait | 72h | - | - | - | - | - | `bet_placed` |
| 5 | Branch | - | `IN SEG_CAN_RECEIVE_BONUS` | - | - | Offer vs exit | - | - |
| 6 | Email | 0 | bonus-eligible | BONUS | Plain offer statement | Reload offer with full terms | first_name | - |
| 7 | Exit | - | - | - | - | - | - | conversion or enters `SEG_DORMANT_30` |

Personalisation block:

```liquid
Hi {{ customer.first_name | default: "there" }},
{% if customer.preferred_product == "sportsbook" %}
  Here are this week's key fixtures.
{% else %}
  Here are the newest games in your favourite category.
{% endif %}
```

Pre-send check request (L4), sample values:

```json
{
  "user_id": "player_12345",
  "journey_id": "JRN_MKT_09_Churn_Prevention",
  "message_type": "promotional",
  "topic": "casino_offers",
  "is_bonus": false
}
```

## Market overlay: DE (Germany)
- Journey modifications: German-language templates on `regulatory_zone == "DE"`.
- Suppression and register: OASIS register match (verify before deployment) sets `self_exclusion_register_match`, which exits the journey.
- Disclosures: helpline BIÖG (formerly BZgA) 0800 1372700 (verify before deployment); licence footer from Customer.io Snippets; 18+ notice.
- RG requirements: safer-gambling footer on every email; statutory limits per counsel.
- Bonus rules: offer email only after counsel confirms DE bonus rules (LQ_LIC_04).

Legal/compliance review required: have qualified legal and compliance counsel review this design in every target jurisdiction before deployment.

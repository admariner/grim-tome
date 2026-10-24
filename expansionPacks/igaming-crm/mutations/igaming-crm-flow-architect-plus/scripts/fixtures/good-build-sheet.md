# Build sheet: gate, dormant reactivation and RG intervention

Workspace: 900001 (sandbox)
Run: dry run
Design: dormant-reactivation-flow.md

## Objects
| Stage | Spec ID | Type | Name | Customer.io ID | Result | State | Topic | Limit | Exit conditions | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | TOP_CASINO_OFFERS | subscription_topic | Casino Offers | dry-run | planned | active | - | - | - | description: TOP_CASINO_OFFERS: casino promotions and bonuses; opt_in true |
| 2 | TOP_SPORTSBOOK_OFFERS | subscription_topic | Sportsbook Offers | dry-run | planned | active | - | - | - | description: TOP_SPORTSBOOK_OFFERS: sportsbook promotions and free bets; opt_in true |
| 2 | TOP_SAFER_GAMBLING | subscription_topic | Safer Gambling | 4 | existing | active | - | - | - | description: TOP_SAFER_GAMBLING: safer gambling messages; opt_in false |
| 3 | SNP_RG_URL | snippet | rg_url | dry-run | planned | active | - | - | - | value from markets.json UK row |
| 4 | SEG_CAN_RECEIVE_MARKETING | segment | SEG_CAN_RECEIVE_MARKETING | dry-run | planned | complete | - | - | - | 15 attribute conditions, flat |
| 4 | SEG_RG_SUPPRESSED | segment | SEG_RG_SUPPRESSED | 12 | existing | complete | - | - | - | count 3 |
| 4 | SEG_FREQUENCY_CAP_REACHED | segment | SEG_FREQUENCY_CAP_REACHED | dry-run | planned | complete | - | - | - | frequency_cap_reached is true |
| 5 | SEG_DORMANT_REACHABLE | segment | SEG_DORMANT_REACHABLE | dry-run | planned | complete | - | - | - | gate conditions inlined; days_since_last_bet 30 to 89 |
| 6 | LIM_EMAIL_MKT_STD | frequency_cap | LIM_EMAIL_MKT_STD | dry-run | planned | active | - | - | - | email 1 per 86400 s; email 4 per 604800 s; retry 86400 s |
| 7 | WHK_L4_VERIFY_SUPPRESSION | webhook_configuration | WHK_L4_VERIFY_SUPPRESSION | dry-run | planned | active | - | - | - | POST to the backend verify endpoint; token added by the user |
| 7 | WHK_REPORTING_COUNTER_FEED | reporting_webhook | WHK_REPORTING_COUNTER_FEED | dry-run | planned | disabled | - | - | - | delivered, opened, clicked, unsubscribed, bounced, complained, converted |
| 8 | JRN_MKT_10_Dormant_Reactivation | automation | JRN_MKT_10_Dormant_Reactivation | dry-run | planned | draft | TOP_CASINO_OFFERS (dry-run) | LIM_EMAIL_MKT_STD (dry-run) | RG_EXIT_BLOCK (SEG_RG_SUPPRESSED 12) | seg_attr trigger SEG_DORMANT_REACHABLE; L4 webhook and branch before each email; Wait Until max 35 d |
| 8 | JRN_MKT_10_Dormant_Reactivation#02-casino | message_action | 02-casino Email: what has changed | dry-run | planned | draft | TOP_CASINO_OFFERS (dry-run) | same as automation | - | MKT; L3 precondition; 02.1 L4 verify and 02.2 L4 branch before it |
| 8 | JRN_MKT_10_Dormant_Reactivation#02-sportsbook | message_action | 02-sportsbook Email: what has changed | dry-run | planned | draft | TOP_SPORTSBOOK_OFFERS (dry-run) | same as automation | - | MKT; topic set per action through subscription_topic_messages/update |
| 8 | JRN_MKT_10_Dormant_Reactivation#05 | message_action | 05 Email: return offer | dry-run | planned | draft | TOP_CASINO_OFFERS (dry-run) | same as automation | - | BONUS; L3 in SEG_CAN_RECEIVE_BONUS |
| 8 | JRN_RG_12_RG_Intervention | automation | JRN_RG_12_RG_Intervention | dry-run | planned | draft | TOP_SAFER_GAMBLING (4) | none | - | event trigger rg_intervention_required; no frequency cap |
| 8 | JRN_RG_12_RG_Intervention#02 | message_action | 02 Email: support and limit tools | dry-run | planned | draft | TOP_SAFER_GAMBLING (4) | none | - | TXN gate |

## Data-model check (stage 1)
Present: all fourteen gate attributes, days_since_last_bet, rg_intervention_required.
Missing: none.

## Not built
None.

## Mechanics to verify in the workspace
frequency_cap_mode value; L4 response capture fields.

## Activation checklist (the user's; nothing was started or sent)
- [ ] Add the bearer token header to `WHK_L4_VERIFY_SUPPRESSION` in the app.
- [ ] Confirm in the app that the MKT_10 exit panel shows the RG exits as one OR group.
- [ ] Author and review every email before switching it to automatic.
- [ ] Run the gate QA cases with a self-excluded test player.
- [ ] Start each automation yourself; MKT_10 without backfill.

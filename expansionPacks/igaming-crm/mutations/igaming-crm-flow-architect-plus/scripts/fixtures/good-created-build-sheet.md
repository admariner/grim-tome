# Build sheet: dormant reactivation, created in the sandbox

Workspace: 900001 (sandbox)
Run: live
Design: dormant-reactivation-flow.md
Pre-flight: stage 1 GO: 14 of 14 gate attributes present and populated on the sample.
Smoke report: SMOKE-REPORT.md, verdict PASS.

## Objects
| Stage | Spec ID | Type | Name | Customer.io ID | Result | State | Topic | Limit | Exit conditions | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | TOP_CASINO_OFFERS | subscription_topic | Casino Offers | 3 | created | active | - | - | - | description: TOP_CASINO_OFFERS: casino promotions and bonuses; opt_in true |
| 4 | SEG_RG_SUPPRESSED | segment | SEG_RG_SUPPRESSED | 12 | existing | complete | - | - | - | count 0 |
| 5 | SEG_DORMANT_REACHABLE | segment | SEG_DORMANT_REACHABLE | 15 | created | complete | - | - | - | count 0 |
| 6 | LIM_EMAIL_MKT_STD | frequency_cap | LIM_EMAIL_MKT_STD | 7 | created | active | - | - | - | email 1 per 86400 s; email 4 per 604800 s |
| 8 | JRN_MKT_10_Dormant_Reactivation | automation | JRN_MKT_10_Dormant_Reactivation | 42 | created | draft | TOP_CASINO_OFFERS (3) | LIM_EMAIL_MKT_STD (7) | RG_EXIT_BLOCK (SEG_RG_SUPPRESSED 12) | seg_attr trigger SEG_DORMANT_REACHABLE |
| 8 | JRN_MKT_10_Dormant_Reactivation#05 | message_action | 05 Email: return offer | 311 | created | draft | TOP_CASINO_OFFERS (3) | same as automation | - | BONUS |

## Activation checklist (the user's; nothing was started or sent)
- [ ] Smoke report: PASS (SMOKE-REPORT.md).
- [ ] Confirm in the app that the exit panel shows the RG exits as one OR group.
- [ ] Start the automation yourself, without backfill.

# Rollback list
| Order | Spec ID | Type | Customer.io ID | Safe removal | Check before | Done |
|---|---|---|---|---|---|---|
| 1 | JRN_MKT_10_Dormant_Reactivation | automation | 42 | Archive | State reads draft | [ ] |
| 2 | LIM_EMAIL_MKT_STD | frequency_cap | 7 | Delete without force | Usage list is empty | [ ] |
| 3 | SEG_DORMANT_REACHABLE | segment | 15 | Archive or delete | Usage list is empty | [ ] |
| 4 | TOP_CASINO_OFFERS | subscription_topic | 3 | Keep unless never assigned and no preference recorded | Topic usage is empty | [ ] |

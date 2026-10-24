# Build sheet: deliberately broken fixture

Run: live

## Objects
| Stage | Spec ID | Type | Name | Customer.io ID | Result | State | Topic | Limit | Exit conditions | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | TOP_CASINO_OFFERS | subscription_topic | Casino Offers | 3 | created | active | - | - | - | opt_in true |
| 3 | SNP_RG_URL | snippet | RG URL | 5 | created | active | - | - | - | value pending |
| 4 | SEG_CAN_RECEIVE_MARKETING | segment | Can receive marketing | 10 | created | complete | - | - | - | display name dropped the spec ID |
| 4 | SEG_CAN_RECEIVE_MARKETING | segment | SEG_CAN_RECEIVE_MARKETING | 11 | created | complete | - | - | - | duplicate from a re-run |
| 4 | SEG_UNSUBSCRIBED | segment | SEG_UNSUBSCRIBED | abc | created | complete | - | - | - | id is not numeric |
| 6 | LIM_EMAIL_MKT_STD | frequency_cap | LIM_EMAIL_MKT_STD |  | created | active | - | - | - | missing id |
| 7 | WHK_REPORTING_COUNTER_FEED | reporting_webhook | WHK_REPORTING_COUNTER_FEED | 8 | created | enabled | - | - | - | enabled by the build |
| 8 | JRN_MKT_09_Churn_Prevention | automation | JRN_MKT_09_Churn_Prevention | 40 | created | running | - | - | exit_campaign when converted | started, no topic, no limit, no RG exits |
| 8 | JRN_VIP_11_VIP_Lifecycle | automation | JRN_VIP_11_VIP_Lifecycle | 41 | created | draft | TOP_TRANSACTIONAL (6) | LIM_EMAIL_MKT_VIP (9) | self_excluded only | wrong topic, missing rows, partial exits |
| 8 | JRN_RG_12_RG_Intervention | automation | JRN_RG_12_RG_Intervention | 42 | created | draft | TOP_CASINO_OFFERS (3) | LIM_EMAIL_MKT_STD (7) | - | RG mail under a marketing topic and a cap |
| 8 | SEG_DORMANT_30 | delete | SEG_DORMANT_30 | 13 | deleted | deleted | - | - | - | global_pause cleanup |
| 8 | MKT_10 | automation | Dormant reactivation | [[ID]] | created | draft | TOP_CASINO_OFFERS (3) | LIM_EMAIL_MKT_STD (7) | RG_EXIT_BLOCK (SEG_RG_SUPPRESSED 12) | spec ID not canonical; TBD |
| 8 | JRN_MKT_10_Dormant_Reactivation#02-sportsbook | message_action | Email: what has changed | 44 | created | automatic | - | same as automation | - | no own topic, wrong name, sending |

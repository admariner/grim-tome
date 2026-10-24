# Smoke report: dormant reactivation

Workspace: 900001 (sandbox)
Run: 20261024-0900
Role map: SEG_CAN_RECEIVE_MARKETING 10, SEG_RG_SUPPRESSED 12, SEG_CAN_RECEIVE_TRANSACTIONAL 11, SEG_CAN_RECEIVE_BONUS 14
Delivery setting: send_to_one
Pre-flight: no running automation or scheduled broadcast could admit a planned profile.

| Case | Profile | Setup | Expected | Observed | Seconds | Result |
|---|---|---|---|---|---|---|
| STRUCT-1 | - | JRN_MKT_10_Dormant_Reactivation exits | RG_EXIT_BLOCK and SEG_RG_SUPPRESSED 12 | as expected | - | PASS |
| G1 | smk-20261024-0900-g1 | all gate conditions pass | in MARKETING and TRANSACTIONAL | as expected | 42 | PASS |
| G2 | smk-20261024-0900-g2 | G1 + self_excluded true | not in MARKETING; in RG_SUPPRESSED | as expected | 40 | PASS |

Verdict: PASS. Nothing was started, sent or deleted; both profiles were created and parked.

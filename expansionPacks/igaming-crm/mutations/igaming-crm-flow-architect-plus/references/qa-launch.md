# QA and launch

Context: the pass/fail QA matrix, the launch sequence and the incident kill
switch. Read it for blueprint section 16, FLOW gate pieces, and the test
evidence part of an audit.

## Contents
- Key idea
- QA matrix
- Launch sequence
- Incident response and kill switch

## Key idea
Suppression tests run first and block everything else: a design that leaks one
marketing email to a self-excluded player fails, whatever else passes. Use
dedicated synthetic test profiles, never real players.

## QA matrix
| ID | Area | Method | Expected result |
|---|---|---|---|
| QA_SUP_01 | Suppression | Set `unsubscribed = true` on an enrolled test profile, trigger a broadcast | 0 marketing sent; profile excluded |
| QA_SUP_02 | Suppression | Set `self_excluded = true` mid-journey | Journey exited; 0 marketing; SE confirmation and transactional mail still delivered |
| QA_SUP_03 | Suppression | Set `timeout_active = true` | Blocked from every MKT and VIP entry |
| QA_SUP_04 | Suppression | Set `aml_status = "blocked"`; separately `kyc_status = "in_progress"` | Marketing suppressed; KYC service mail delivered |
| QA_SUP_05 | Suppression | Set `rg_risk_level = "high"` and `"severe"` | 0 marketing; RG_12 triggered |
| QA_SUP_06 | Suppression | Set `rg_risk_level = "medium"` | No bonus email; at most 1 marketing email in 7 days |
| QA_SUP_08 | Suppression | Register an unverified test profile, then set `self_excluded = true` (separately `self_exclusion_register_match = true`, then `timeout_active = true`) before the 24h TXN_01 wait ends | TXN_01 exits; the verification reminder is never sent |
| QA_SUP_07 | Suppression | Self-exclude a test profile, then look it up in Customer.io | Profile still exists with `self_excluded = true` (never suppressed or deleted); SE confirmation delivered |
| QA_GATE_01-10 | L4 gate | Cases in the suppression gate reference | All pass |
| QA_SLA_01 | SLA | Self-exclude via UI, read the audit log | Fully suppressed in at most 300 s |
| QA_SLA_02 | SLA | Change `vip_tier` in backend | Profile updated within 15 min |
| QA_REC_01 | Reconciliation | Set `self_excluded = true` in the backend only | CRITICAL alert, broadcasts blocked |
| QA_CAP_01 | Caps | Send 2 marketing emails to an active_casual profile, trigger a 3rd | 3rd blocked |
| QA_CAP_02 | Caps | Second email 12 h after the first with a 24 h cooldown | Held until cooldown ends |
| QA_CAP_03 | Caps | VIP profile, 6th marketing email in 7 days | 6th blocked |
| QA_CAP_04 | Caps | active_core + rg_medium profile | Most restrictive caps applied (1/week, no bonus) |
| QA_CAP_05 | Caps | Message hits the daily rule of `LIM_EMAIL_MKT_STD` with no retry window | Logged Undeliverable; person continues the journey |
| QA_CAP_06 | Caps | RG_12 email to a profile at its marketing limit | Delivered (RG automations have no limit assigned) |
| QA_JRN_01 | Journey logic | Fire the trigger twice within 1 h | One enrolment |
| QA_JRN_02 | Journey logic | Waits and quiet hours | Sends within 5 min of schedule in player zone |
| QA_JRN_03 | Journey logic | Each branch condition with matching profiles | 100% correct routing |
| QA_JRN_04 | Journey logic | Convert mid-journey | Immediate exit |
| QA_REN_01 | Rendering | Profile missing `first_name` and other optional fields | Fallbacks render; no raw Liquid |
| QA_REN_02 | Rendering | Each currency and locale | Correct symbols and decimals |
| QA_REN_03 | Rendering | Cross-client rendering | No broken layouts |
| QA_UNS_01 | Unsubscribe | One-click unsubscribe from a mailbox provider | Topic or global unsubscribe applied without login |
| QA_UNS_02 | Unsubscribe | Toggle each topic in the preference centre | Backend and Customer.io states match |
| QA_RG_01 | RG | Raise a test profile to medium | RG_12 enrolment within 15 min; email within 24 h |
| QA_RG_02 | RG | Spending summary for a test ledger | Figures match the ledger exactly |
| QA_CMP_01 | Compliance | Inspect every marketing template | 18+, RG link, zone helpline, licence footer, address present |
| QA_CMP_02 | Compliance | Inspect every transactional and RG template | No promotional content |
| QA_DEL_01 | Deliverability | SPF, DKIM, DMARC checks | All pass |
| QA_DEL_02 | Deliverability | Warm-up plan review | Volume ramp configured |
| QA_DAT_01 | Data | Fire every event from staging | 0 schema errors |

## Launch sequence
1. Sandbox: every QA case on synthetic profiles in a staging workspace.
2. Internal pilot: a small cohort of staff test accounts on production data
   paths; measure SE propagation and confirm zero leakage.
3. Compliance sign-off: legal and compliance approve templates, gate, RG
   flows and overlays in writing.
4. Graduated ramp: transactional and RG journeys first, then marketing at 10%
   of the eligible base, increasing only while leakage stays 0, bounce under
   0.8% and complaints under 0.05%.

## Incident response and kill switch
1. Kill switch: set `marketing_blocked = true` for the affected scope (all
   players through a backend batch identify, or one zone). `RG_EXIT_BLOCK`
   exits everyone from marketing automations, `SEG_CAN_RECEIVE_MARKETING`
   blocks new entries, and the L4 endpoint returns `can_receive_marketing =
   false`. Then stop each Layer-3 automation and broadcast from the runbook
   list with "Force people to exit immediately"; this stops further sends,
   but messages already sent cannot be recalled. RG and transactional
   journeys keep running.
2. Isolate: list profiles that received marketing while suppressed (send log
   joined to the audit log).
3. Root cause within 2 hours: webhook errors, schema mismatches, segment logic,
   template errors.
4. Fix in staging, re-run QA_SUP_01-06 and QA_GATE_01-10, obtain compliance
   sign-off, then ramp again from step 4 of the launch sequence.

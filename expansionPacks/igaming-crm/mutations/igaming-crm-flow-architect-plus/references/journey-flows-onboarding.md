# Journey flows: onboarding

Context: full specs and flow tables for TXN_01, SVC_02, MKT_03, MKT_04 and
MKT_05. Read the one you need when writing blueprint sections 7-8 or a FLOW
journey, then adapt it to the intake answers.

## Contents
- How to read these tables
- JRN_TXN_01_Email_Verification
- JRN_SVC_02_KYC_Completion
- JRN_MKT_03_No_Deposit_Activation
- JRN_MKT_04_First_Deposit_Welcome
- JRN_MKT_05_First_Play_Activation

## How to read these tables
Gate `MKT` on an Email row means, in the journey builder: an action condition
(in `SEG_CAN_RECEIVE_MARKETING`, not in `SEG_FREQUENCY_CAP_REACHED`), then the
L4 webhook action and its true/false branch, then the email. `BONUS` adds the
`SEG_CAN_RECEIVE_BONUS` action condition. `TXN` is the transactional gate.
`RG_EXIT_BLOCK` is the standard exit block in `templates/rg-exit-block.md`.
TXN and SVC templates send even when their Liquid fails, so every variable in
them has a fallback (validator rule C29).

## JRN_TXN_01_Email_Verification
| Dimension | Specification |
|---|---|
| journey_id | `JRN_TXN_01_Email_Verification` |
| type | Transactional |
| trigger | `registered` |
| entry_conditions | `email_verified != true` only (true for every new registrant, including unset). `account_status` is not in the `registered` payload and syncs within 5 minutes, so it is checked at step 3, after the first wait, and by the custom exits |
| exit_conditions | `email_verified == true`; `account_status` changes to suspended, restricted or closed; `self_excluded` changes to true; `self_exclusion_register_match` changes to true; `timeout_active` changes to true |
| subscription_topic | Transactional |
| suppression_checks | Verification exception: the address is not verified yet, so `SEG_CAN_RECEIVE_TRANSACTIONAL` (which needs `email_verified == true`) cannot gate these emails; the first email uses the action condition `account_status != "closed"` plus the three RG conditions, and the reminder also requires the step-3 RG conditions (`self_excluded != true AND self_exclusion_register_match != true AND timeout_active != true`). Not marketing-gated |
| frequency_cap | Exempt |
| flow_steps | Verification email; reminder after 24h; final reminder after 48h; flag for review |
| wait_times | 0, 24h, 48h |
| branch_logic | `email_verified == true` checked before each reminder |
| email_purpose | Deliver the verification link and explain what verification unlocks |
| personalisation_fields | `customer.first_name` (default "there"), `event.verification_url` (default `snippets.verify_help_url`, the account page that re-sends the link) |
| conversion_event | `email_verified` |
| guardrail_metrics | Verification rate within 72h; bounce below 1%; delivery above 99.5% |
| compliance_notes | No offer, bonus or deposit prompt before age and identity verification |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Email | 0 | `account_status != "closed" AND self_excluded != true AND self_exclusion_register_match != true AND timeout_active != true` (verification exception) | TXN | Direct: verify your email | Verification link, security note | first_name, verification_url | - |
| 2 | Wait | 24h | - | - | - | - | - | `email_verified == true` |
| 3 | Branch | - | `email_verified != true AND account_status NOT IN ["suspended","restricted","closed"] AND self_excluded != true AND self_exclusion_register_match != true AND timeout_active != true` (synced by now) | - | - | Unverified, open, not excluded: continue | - | otherwise exit |
| 4 | Email | 0 | - | TXN | Reminder: one step left | Link again, help contact | first_name, verification_url | - |
| 5 | Wait | 48h | - | - | - | - | - | `email_verified == true` |
| 6 | Webhook | 0 | `email_verified != true` | - | - | Flag account for review in backend | user_id | - |
| 7 | Exit | - | - | - | - | - | - | Journey complete |

## JRN_SVC_02_KYC_Completion
| Dimension | Specification |
|---|---|
| journey_id | `JRN_SVC_02_KYC_Completion` |
| type | Service |
| trigger | `kyc_required` (normalised event; reason `kyc_started`, `withdrawal_requested` or `deposit_threshold`, sent by the backend for each cause) |
| entry_conditions | `kyc_status NOT IN ["approved","provisional_allowed"] AND account_status == "active"` (steady-state values the trigger does not change, so no sync lag) |
| exit_conditions | `kyc_approved` with event time after the trigger; `account_status == "suspended"`; 7 d elapsed |
| subscription_topic | Transactional |
| suppression_checks | `SEG_CAN_RECEIVE_TRANSACTIONAL`; AML hold: every Email row carries the action condition `aml_status != "frozen"` (SYS_13 handles frozen accounts) |
| frequency_cap | Exempt |
| flow_steps | Document request; reminder 24h; final notice 48h before withdrawal restriction |
| wait_times | 0, 24h, 48h |
| branch_logic | `kyc_status == "approved"` exits; `kyc_status == "rejected"` sends resubmission guidance |
| email_purpose | Request documents, explain why and how to upload |
| personalisation_fields | `customer.first_name` (default "there"), `event.upload_url` (default `snippets.kyc_upload_url`), `event.reason` (default "account verification") |
| conversion_event | `kyc_approved` |
| guardrail_metrics | KYC completion within 72h; time to approval |
| compliance_notes | Service tone; no offers; states what verification unlocks (withdrawals) |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Email | 0 | `aml_status != "frozen"` | TXN | Action needed: verify your identity | Required documents, upload link | first_name, upload_url | - |
| 2 | Wait | 24h | - | - | - | - | - | `kyc_approved` after the trigger |
| 3 | Branch | - | `kyc_status == "rejected"` | - | - | Rejected path vs pending path | kyc_status | - |
| 4 | Email | 0 | rejected and `aml_status != "frozen"` | TXN | Your documents need another look | Resubmission guidance | first_name, upload_url | - |
| 5 | Email | 0 | pending and `aml_status != "frozen"` | TXN | Reminder: finish verification | Steps left, support link | first_name, upload_url | - |
| 6 | Wait | 48h | - | - | - | - | - | `kyc_approved` after the trigger |
| 7 | Email | 0 | `kyc_status != "approved" AND aml_status != "frozen"` | TXN | Final notice before withdrawal restriction | What changes and when | first_name | - |
| 8 | Exit | - | - | - | - | - | - | `kyc_approved` after the trigger, or 7 d |

## JRN_MKT_03_No_Deposit_Activation
| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_03_No_Deposit_Activation` |
| type | Marketing |
| trigger | Person enters `SEG_NO_DEPOSIT_ELIGIBLE` (which already includes `IN SEG_CAN_RECEIVE_MARKETING`; segment trigger, so it fires only once `kyc_status == "approved"` has synced, and picks up a player who becomes marketing-eligible later, as MKT_10 does; activation: only future additions) |
| entry_conditions | `IN SEG_NO_DEPOSIT_ELIGIBLE` (includes `SEG_CAN_RECEIVE_MARKETING`) |
| exit_conditions | `deposit_successful` after the trigger; 14 d elapsed; `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`) |
| subscription_topic | Casino Offers; Sportsbook Offers when `preferred_product == "sportsbook"` |
| suppression_checks | L2 entry; L3 and L4 before every email (Gate column); offer email adds `SEG_CAN_RECEIVE_BONUS`; UK adds the product's consent segment (`SEG_CONSENT_CASINO_EMAIL` or `SEG_CONSENT_BETTING_EMAIL`) per product branch |
| frequency_cap | new_registrant: 1/day, 3/week, 24h cooldown, 2 bonus/week |
| flow_steps | Product introduction; how deposits and safer-play tools work; welcome offer or content-only variant |
| wait_times | 2h, 48h, 72h |
| branch_logic | `preferred_product` picks casino or sportsbook content; `lifetime_deposits == 0` before each email; offer only when in `SEG_CAN_RECEIVE_BONUS`, else content-only; first-play-only zones (SE) send the offer only at the first play occasion, checking `first_play_bonus_used != true` |
| email_purpose | Orient the new player and present the welcome offer with its terms |
| personalisation_fields | `customer.first_name` (default "there"), `customer.preferred_product`, `customer.currency` |
| conversion_event | `deposit_successful` with `deposit_number == 1` |
| guardrail_metrics | Registration-to-first-deposit rate; unsubscribe below 0.5%; complaint below 0.05% |
| compliance_notes | 18+ notice and safer-gambling link in every email; wagering terms in the offer email; no pressure framing |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Wait | 2h | - | - | - | - | - | `deposit_successful` |
| 2 | Email | 0 | `preferred_product` casino or sportsbook variant | MKT | Benefit-led welcome | Product tour by preference | first_name, preferred_product | - |
| 3 | Wait | 48h | - | - | - | - | - | `deposit_successful` |
| 4 | Email | 0 | `lifetime_deposits == 0` | MKT | Practical: how to get started | Deposit methods, limits and safer-play tools | first_name, currency | - |
| 5 | Wait | 72h | - | - | - | - | - | `deposit_successful` |
| 6 | Branch | - | `IN SEG_CAN_RECEIVE_BONUS` | - | - | Offer vs content-only | - | - |
| 7 | Email | 0 | bonus-eligible | BONUS | Clear offer statement | Welcome bonus with wagering terms and expiry | first_name, currency | - |
| 8 | Email | 0 | not bonus-eligible | MKT | Discovery | Game or market highlights, no offer | first_name, preferred_product | - |
| 9 | Exit | - | - | - | - | - | - | `deposit_successful` or 14 d |

## JRN_MKT_04_First_Deposit_Welcome
| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_04_First_Deposit_Welcome` |
| type | Marketing |
| trigger | `deposit_successful` where `event.deposit_number == 1` |
| entry_conditions | `IN SEG_CAN_RECEIVE_MARKETING AND event.deposit_number == 1` (keyed on the trigger payload, not on `lifetime_deposits`, so entry never races the profile update) |
| exit_conditions | second `deposit_successful` (event time after the trigger); 7 d elapsed; `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`) |
| subscription_topic | Casino Offers or Sportsbook Offers by `preferred_product` |
| suppression_checks | L2 entry; L3 and L4 per email; bonus reminder adds `SEG_CAN_RECEIVE_BONUS`; UK: every email adds the product's consent attribute (`consent_betting_email == true` for a sportsbook welcome) |
| frequency_cap | first_depositor: 1/day, 4/week, 24h cooldown, 1 bonus/week (MKT_04 uses at most 3 slots: days 0, 1, 4; the fourth is reserved for MKT_05) |
| flow_steps | Welcome and how the bonus works; bonus activation reminder if unclaimed; limits and loyalty introduction |
| wait_times | 0, 24h, 72h |
| branch_logic | `active_bonus_id` set or not; `preferred_product` content variant |
| email_purpose | Confirm the start, explain bonus terms, introduce limits and loyalty |
| personalisation_fields | `customer.first_name` (default "there"), `customer.active_bonus_id`, `customer.wagering_progress_pct` (default 0), `customer.vip_tier` |
| conversion_event | `deposit_successful` with `deposit_number == 2`; `first_game_played` |
| guardrail_metrics | First-to-second deposit rate; bonus take-up; unsubscribe below 0.5% |
| compliance_notes | The deposit receipt itself is a separate transactional message (SYS_13); wagering terms in every bonus email; the welcome offer gets a Bonus terms row per market (UK: one product, wagering at most 10x; BR: no deposit-conditional reward, so content only) |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Branch | - | `IN SEG_CAN_RECEIVE_BONUS` | - | - | Bonus welcome vs plain welcome | - | - |
| 1a | Email | 0 | bonus-eligible | BONUS | Welcome aboard | How the welcome bonus works, terms | first_name, active_bonus_id | - |
| 1b | Email | 0 | not bonus-eligible | MKT | Welcome aboard | Getting started, limits and safer-play tools | first_name | - |
| 2 | Wait | 24h | - | - | - | - | - | second deposit |
| 3 | Branch | - | `active_bonus_id` is not set | - | - | Unclaimed vs claimed | active_bonus_id | - |
| 4 | Email | 0 | unclaimed | BONUS | Reminder of what is available | How to activate the bonus, terms | first_name | - |
| 5 | Wait | 72h | - | - | - | - | - | second deposit |
| 6 | Email | 0 | - | MKT | Getting more from your account | Deposit limits, reality checks, loyalty basics | first_name, vip_tier | - |
| 7 | Exit | - | - | - | - | - | - | 7 d |

## JRN_MKT_05_First_Play_Activation
| Dimension | Specification |
|---|---|
| journey_id | `JRN_MKT_05_First_Play_Activation` |
| type | Marketing |
| trigger | Person enters `SEG_FIRST_DEPOSIT_NO_PLAY` |
| entry_conditions | `IN SEG_CAN_RECEIVE_MARKETING AND IN SEG_FIRST_DEPOSIT_NO_PLAY` |
| exit_conditions | `first_game_played`; `bet_placed`; 7 d elapsed; `RG_EXIT_BLOCK` (includes `SEG_RG_SUPPRESSED`) |
| subscription_topic | Casino Offers or Sportsbook Offers by `preferred_product` |
| suppression_checks | L2 entry; L3 and L4 per email |
| frequency_cap | first_depositor: 1/day, 4/week, 24h cooldown; MKT_05 sends one email, the slot MKT_04 leaves free |
| flow_steps | One getting-started email by preference, about 60 hours after the first deposit, between MKT_04's day-1 and day-4 emails |
| wait_times | 36h after segment entry (entry is about 24h after the deposit), so the email lands about 36h from each MKT_04 email and clears the 24h cooldown |
| branch_logic | `preferred_product == "sportsbook"` sends markets content, else games content |
| email_purpose | Help a funded player find a first game or market |
| personalisation_fields | `customer.first_name` (default "there"), `customer.preferred_sport`, `customer.preferred_casino_category` |
| conversion_event | `first_game_played` |
| guardrail_metrics | Deposit-to-first-play rate; unsubscribe below 0.5% |
| compliance_notes | Content only, no offer; safer-gambling link |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Wait | 36h | - | - | - | - | - | `first_game_played` |
| 2 | Branch | - | `preferred_product == "sportsbook"` | - | - | Sports vs casino content | preferred_product | - |
| 3 | Email | 0 | sportsbook | MKT | Helpful: how to place a first bet | Markets guide | first_name, preferred_sport | - |
| 4 | Email | 0 | casino or other | MKT | Helpful: where to start | Game categories guide and popular titles | first_name, preferred_casino_category | - |
| 5 | Exit | - | - | - | - | - | - | `first_game_played`, `bet_placed`, or 7 d |

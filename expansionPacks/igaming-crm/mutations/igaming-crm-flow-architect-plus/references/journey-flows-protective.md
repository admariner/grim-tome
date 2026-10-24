# Journey flows: protective and system

Context: full specs and flow tables for RG_12, SYS_13, SYS_14 and SYS_15. Read
the one you need for blueprint sections 7-8 and 10, or a FLOW journey or rg
piece. All four use the transactional gate, carry no offers and are cap-exempt
(no frequency cap assigned). Each triggers on one event; the backend sends a
normalised event with a reason field for journeys with several causes. Every
Liquid variable has a fallback (validator rule C29).

## Contents
- JRN_RG_12_RG_Intervention
- JRN_SYS_13_Account_Compliance_Status
- JRN_SYS_14_Preference_Confirmation
- JRN_SYS_15_Sunset_List_Hygiene

## JRN_RG_12_RG_Intervention
| Dimension | Specification |
|---|---|
| journey_id | `JRN_RG_12_RG_Intervention` |
| type | Responsible gambling |
| trigger | `rg_intervention_required` (normalised event; `event.reason` is one of risk_escalated, signal_detected, limit_removed, loss_limit, session_limit, timeout_started, self_exclusion_started; `event.risk_level` carries the level at send time) |
| entry_conditions | Keyed on the trigger payload, never on attributes that sync 5-15 minutes later: `event.reason IN ["timeout_started","self_exclusion_started","limit_removed","loss_limit","session_limit"] OR event.risk_level IN ["medium","high","severe"]`. A low-risk player hitting a limit, and a player whose `self_excluded` or `rg_risk_level` has not synced yet, still enter at once |
| exit_conditions | Recorded review sets `rg_risk_level == "low"`: not a custom exit; handled at step 8 (the 7-day review, after sync); timeout or SE confirmation sent (suppression persists through segment flags); low-risk limit-event email sent |
| subscription_topic | Safer Gambling (mandatory, non-marketing) |
| suppression_checks | `SEG_CAN_RECEIVE_TRANSACTIONAL` only; never suppressed by the marketing gate or topic unsubscribes |
| frequency_cap | Exempt |
| flow_steps | Branch by situation; medium: safer-play tools email, 7 d review; high or severe: case-queue webhook, host notice for VIPs, protective email, 7 d review; timeout or SE: confirmation |
| wait_times | 0 (email within 24h for medium, 2h for high and severe), 7 d review |
| branch_logic | Steps 1-3 branch on the payload only: `event.reason IN ["timeout_started","self_exclusion_started"]`; limit reason with `event.risk_level == "low"`; `event.risk_level == "medium"`; `event.risk_level IN ["high","severe"]`. `vip_status != "standard"` adds the host webhook (attribute may lag 15 minutes; the backend also sends the VIP flag in the case-queue call). `rg_risk_level` is read only at the 7-day review |
| email_purpose | Protective information: limits, reality checks, timeout and self-exclusion options, helpline |
| personalisation_fields | `customer.first_name` (default "there"), `customer.regulatory_zone` (helpline block via the `rg_footer` snippet), `snippets.limits_url` (default "your account settings"), `snippets.rg_url` (default "https://www.begambleaware.org") |
| conversion_event | `limit_set`; `timeout_started`; `self_exclusion_started` |
| guardrail_metrics | Time from escalation to email (medium 24h, high 2h); response rate; limit-adoption rate |
| compliance_notes | Zero promotional content; helpline for the player's zone; monitor-only metrics, never an A/B test on suppression or delay |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Branch | - | `event.reason IN ["timeout_started","self_exclusion_started"]` | - | - | Confirmation path vs risk path | reason | - |
| 2 | Email | 0 | SE or timeout | TXN | Confirmation, plain | Confirms exclusion or timeout, end date, support services | first_name, regulatory_zone | exit after send |
| 2a | Branch | - | `event.reason IN ["limit_removed","loss_limit","session_limit"]` and `event.risk_level == "low"` | - | - | Low-risk limit path vs risk path | risk_level | - |
| 2b | Email | 0 | low-risk limit event | TXN | Factual limit notice | Which limit was reached or removed, how limits work, safer-play tools, helpline; never an invitation to raise a limit | first_name, regulatory_zone | exit after send |
| 3 | Branch | - | `event.risk_level == "medium"` | - | - | Medium vs high/severe | risk_level | - |
| 4 | Email | 0 | medium | TXN | Supportive check-in | Deposit limits, reality checks, self-assessment, helpline | first_name, regulatory_zone | - |
| 5 | Webhook | 0 | `event.risk_level IN ["high","severe"]` | - | - | Open RG case; notify VIP host when `vip_status != "standard"` | user_id, risk_level | - |
| 6 | Email | 0 | high or severe | TXN | Direct and caring | Limits, timeout, self-exclusion, helpline | first_name, regulatory_zone | - |
| 7 | Wait | 7 d | - | - | - | - | - | review sets low |
| 8 | Branch | - | `rg_risk_level == "low"` (attribute synced long before day 7) | - | - | Reviewed down vs persisting | rg_risk_level | low: exit |
| 9 | Email | 0 | still medium or above | TXN | Follow-up check-in | Tools again, how to reach support | first_name, regulatory_zone | - |
| 10 | Exit | - | - | - | - | - | - | review complete |

## JRN_SYS_13_Account_Compliance_Status
| Dimension | Specification |
|---|---|
| journey_id | `JRN_SYS_13_Account_Compliance_Status` |
| type | System |
| trigger | `account_notice_required` (normalised event; `event.notice_type` is one of password_reset, security_alert, withdrawal_completed, account_suspended, account_closed, aml_status_changed, fraud_or_bonus_abuse_flagged) |
| entry_conditions | The trigger event. No segment filter on entry, because the closure notice arrives after `identify()` has already set `account_status = "closed"` |
| exit_conditions | After the email is sent |
| subscription_topic | Transactional |
| suppression_checks | `SEG_CAN_RECEIVE_TRANSACTIONAL` on every email except the closure notice, which uses the closure exception (`email_verified == true` only, see the segment library) so it sends even when the closed status arrives first |
| frequency_cap | Exempt |
| flow_steps | Route by event type; one email; exit |
| wait_times | immediate |
| branch_logic | `event.notice_type` routes to the matching template; AML and fraud notices only where legally permitted to inform (tipping-off rules) |
| email_purpose | Security, account-status and payment confirmations |
| personalisation_fields | `customer.first_name` (default "there"), `event.amount` (default "see account"), `event.currency` (default "EUR"), `event.requested_at` (default "recently") |
| conversion_event | n/a (no conversion goal) |
| guardrail_metrics | Delivery above 99.5%; latency under 10 s |
| compliance_notes | No promotional content; AML and fraud wording approved by compliance |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Branch | - | `event.notice_type` | - | - | Route to template | - | - |
| 2 | Email | 0 | password_reset or security_alert | TXN | Security notice | Reset link or alert details | first_name, requested_at | - |
| 3 | Email | 0 | withdrawal_completed | TXN | Payment confirmation | Amount, method, timing | first_name, amount, currency | - |
| 4 | Email | 0 | account_suspended | TXN | Account status notice | What changed, how to contact support | first_name | - |
| 5 | Email | 0 | account_closed | TXN (closure exception: `email_verified == true` only) | Closure confirmation | Closure date, how to withdraw any balance, data and contact information | first_name | - |
| 6 | Email | 0 | aml_status_changed to blocked, frozen or restricted | TXN | Account review notice | Account under review, what the player can and cannot do, how to contact support; compliance-approved wording that does not disclose an AML investigation | first_name | - |
| 7 | Email | 0 | fraud_or_bonus_abuse_flagged | TXN | Account review notice | Bonus or account restriction in neutral terms, how to contact support; compliance-approved wording | first_name | - |
| 8 | Exit | - | - | - | - | - | - | after send |

## JRN_SYS_14_Preference_Confirmation
| Dimension | Specification |
|---|---|
| journey_id | `JRN_SYS_14_Preference_Confirmation` |
| type | System |
| trigger | `unsubscribe_updated` |
| entry_conditions | The trigger event |
| exit_conditions | After the confirmation is sent |
| subscription_topic | Transactional |
| suppression_checks | `SEG_CAN_RECEIVE_TRANSACTIONAL` |
| frequency_cap | Exempt |
| flow_steps | Sync state to backend; one confirmation email; exit |
| wait_times | immediate |
| branch_logic | `event.topic == "all"` (global) vs single topic; when the backend sends a product x channel change (UK consent), `event.product` and `event.channel` select the product-channel confirmation |
| email_purpose | Confirm what the player will and will not receive |
| personalisation_fields | `customer.first_name` (default "there"), `event.topic` (default "your marketing preferences"), `event.action` (default "updated"), `event.product` and `event.channel` (default "this product" / "this channel") |
| conversion_event | n/a (no conversion goal) |
| guardrail_metrics | Backend sync success 100%; unsubscribe latency under 30 s |
| compliance_notes | Confirms RG and service mail continue; no win-back content |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Webhook | 0 | - | - | - | Sync preference state to backend | user_id, topic, action | - |
| 2 | Email | 0 | `event.topic == "all"` | TXN | Confirmation | Global opt-out confirmed; service and RG mail continue | first_name | - |
| 3 | Email | 0 | single topic and `event.product` not set | TXN | Confirmation | Topic change confirmed; link to preference centre | first_name, topic | - |
| 3a | Email | 0 | `event.product` set (takes precedence over step 3; steps 2, 3 and 3a are mutually exclusive) | TXN | Confirmation | Which product and channel changed; other products and channels unchanged | first_name, product, channel | - |
| 4 | Exit | - | - | - | - | - | - | after send |

## JRN_SYS_15_Sunset_List_Hygiene
| Dimension | Specification |
|---|---|
| journey_id | `JRN_SYS_15_Sunset_List_Hygiene` |
| type | System |
| trigger | Person is in both `SEG_DORMANT_90` and `SEG_EMAIL_UNENGAGED` (daily check); MKT_10 hands over at day 90 by leaving the dormant ladder |
| entry_conditions | `IN SEG_DORMANT_90 AND IN SEG_EMAIL_UNENGAGED AND sunset_suppressed != true` |
| exit_conditions | Any open or click (`last_email_engagement_at` within 7 d); `sunset_suppressed == true` set |
| subscription_topic | Transactional |
| suppression_checks | `SEG_CAN_RECEIVE_TRANSACTIONAL`; content contains no offer |
| frequency_cap | Exempt |
| flow_steps | One keep-in-touch email; wait 7 d; if no engagement, set `sunset_suppressed = true` |
| wait_times | 0, 7 d |
| branch_logic | Engagement in the 7 d window; `real_money_balance > 0` keeps balance notices active |
| email_purpose | Ask whether the player wants to keep receiving email |
| personalisation_fields | `customer.first_name` (default "there"), the Customer.io `manage_subscription_preferences_url` link tag |
| conversion_event | `last_email_engagement_at` updated (click on keep-me-subscribed) |
| guardrail_metrics | Bounce rate trend; inbox placement |
| compliance_notes | No offer; data-minimisation review for long-dormant profiles goes to counsel |

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | Email | 0 | - | TXN | Plain question | Keep receiving email? One-click keep or manage preferences | first_name, preferences_url | - |
| 2 | Wait | 7 d | - | - | - | - | - | click or open |
| 3 | Webhook | 0 | no engagement | - | - | Set `sunset_suppressed = true` in backend and profile | user_id | - |
| 4 | Exit | - | - | - | - | - | - | flag set |

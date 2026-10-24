# Build sheet: suppression gate and lifecycle segments

Workspace: 900001 (sandbox)
Run: dry run
Design: gate-and-lifecycle-segments.md
Pre-flight: stage 1 NO-GO: self_excluded, timeout_active and rg_risk_level absent from GET /attributes; kyc_status values none, partial, pending, approved (transform proposed).
Pre-flight: stage 2 NO-GO: subscription_center_enabled false; 0 topics.
Pre-flight: stage 3 GO: GET /snippets answered.
Pre-flight: stage 4 NO-GO: data_driven_segments_allotted 0, has_data_driven_segments_addon false; 4 segment creates planned.
Pre-flight: stage 6 GO: email and webhook supported; scoped cap LIM_EMAIL_MKT_STD is email.
Pre-flight: stage 7 NO-GO: GET /webhooks returned 403 on this token.
Pre-flight: stage 8b GO: identifier_type id; delivery_settings send_to_one.
Stopped at stage 1: gate attributes self_excluded, timeout_active and rg_risk_level are not in the workspace data index.

## Objects
| Stage | Spec ID | Type | Name | Customer.io ID | Result | State | Topic | Limit | Exit conditions | Notes |
|---|---|---|---|---|---|---|---|---|---|---|

## Data-model check (stage 1)
Present: email_verified, created_at.
Missing: self_excluded, timeout_active, rg_risk_level.
Operator field mapping (confirmed by the user): none.

## Not built
Every object in scope: SEG_CAN_RECEIVE_MARKETING, SEG_RG_SUPPRESSED, SEG_NEW_REGISTRANT, SEG_NO_DEPOSIT_ELIGIBLE.

## Mechanics to verify in the workspace
None reached.

## Activation checklist (the user's; nothing was started or sent)
- [ ] Send the missing gate attributes from the backend, then re-run BUILD.
- [ ] Before the re-run, clear the other NO-GO stages: enable the subscription center in the app, get a data-driven segment allowance, use a token with webhook access.

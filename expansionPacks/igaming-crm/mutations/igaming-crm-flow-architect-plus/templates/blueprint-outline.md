# [[OPERATOR_OR_PROJECT_NAME]] CRM Blueprint

Fill guide (delete this block, down to and including the marker line, once
every section is written):
- Top: the `banner` of each closed_pending market (markets.json) above the title.
- 1: 3-layer model table, component diagram or table, backend-to-CRM data
  flow, governance (access, dual sign-off, audit, kill switch), licence posture.
- 2: attribute table (attribute, type, example, purpose, source, used for),
  enums, sync SLAs, operator field mapping.
- 3: event table (event, fires when, required, optional, journeys,
  conversion), example payloads, webhooks back, operator events.
- 4: segment table (segment, purpose, logic, journeys, suppression, priority)
  with exact logic for every segment.
- 5: gate pseudocode, L1-L4 table, L4 request/response/branch, `RG_EXIT_BLOCK`, SLA
  budget, reconciliation, audit log, downtime; accepted-risk flag only if signed.
- 6: six-topic table, unsubscribe mechanics, consent posture, footer.
- 7: catalogue table, then one 16-dimension spec per journey.
- 8: one flow table per journey with the Gate column.
- 9: content matrix (journey, email, purpose, subject approach, content type,
  personalisation, offer type, RG requirement, compliance notes, rg_content_check).
- 10: signals, level actions, bonus table, VIP rules, RG_12, spending summary.
- 11: cap table, evaluation order, most-restrictive rule, counters, implementation.
- 12: 11-level priority table, conflict matrix, pause versus exit.
- 13: KPI table per family (definition, calculation, target, alert, source),
  refresh tiers.
- 14: approved and prohibited categories, design standards, RG constraints,
  quarterly calendar.
- 15: phase tables (task, owner, dependency, effort days).
- 16: QA matrix (ID, area, method, expected), launch sequence, kill switch.
- 17: question tables by category (ID, question, why, action if unclear).
[[DELETE_FILL_GUIDE_ABOVE]]

Assumptions: [[ASSUMPTIONS_FROM_INTAKE]]

## 1. Executive CRM Architecture
[[LAYER_MODEL_TABLE]]
[[COMPONENTS_AND_DATA_FLOW]]
[[GOVERNANCE_AND_LICENCE_POSTURE]]

## 2. Customer/Profile Attribute Schema
[[ATTRIBUTE_TABLE]]
[[ENUMS_AND_SYNC_SLAS]]

## 3. Event Taxonomy
[[EVENT_TABLE]]
[[EXAMPLE_PAYLOADS_AND_WEBHOOKS]]

## 4. Master Segments
[[SEGMENT_TABLE]]

## 5. Global Suppression Framework
[[GATE_PSEUDOCODE]]
[[L1_L4_IMPLEMENTATION]]
[[EXIT_SET_SLA_BACKSTOPS]]

## 6. Subscription Center and Topics
[[TOPIC_TABLE]]
[[UNSUBSCRIBE_MECHANICS]]

## 7. Journey Map
[[JOURNEY_CATALOGUE_TABLE]]
[[JOURNEY_SPECS]]

## 8. Detailed Flow Logic
[[FLOW_TABLES]]

## 9. Email Content Matrix
[[CONTENT_MATRIX]]

## 10. Responsible Gambling Automation
[[RG_SIGNALS_ACTIONS_BONUS_VIP]]
[[RG_12_AND_SPENDING_SUMMARY]]

## 11. Frequency Caps
[[CAP_TABLE]]
[[CAP_EVALUATION_AND_COUNTERS]]

## 12. Prioritisation and Conflict Rules
[[PRIORITY_TABLE]]
[[CONFLICT_MATRIX_AND_PAUSE_EXIT]]

## 13. Reporting Dashboard
[[KPI_TABLES]]

## 14. A/B Testing Framework
[[AB_RULES_AND_CALENDAR]]

## 15. Implementation Checklist
[[PHASE_TABLES]]

## 16. QA and Launch Checklist
[[QA_MATRIX_LAUNCH_KILL_SWITCH]]

## 17. Legal/Compliance Questions
[[LEGAL_QUESTION_TABLES]]

## Appendix A. Market Overlays
[[ONE_OVERLAY_BLOCK_PER_MARKET]]

Legal/compliance review required: have qualified legal and compliance counsel review this design in every target jurisdiction before deployment.

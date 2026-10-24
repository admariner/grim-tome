### [[JOURNEY_ID]]

| Dimension | Specification |
|---|---|
| journey_id | `[[JOURNEY_ID]]` |
| type | [[TYPE]] |
| trigger | [[TRIGGER_EVENT_OR_SEGMENT_ENTRY]] |
| entry_conditions | [[ENTRY_CONDITIONS]] |
| exit_conditions | [[EXIT_CONDITIONS]] |
| subscription_topic | [[TOPIC]] |
| suppression_checks | [[GATE_LAYERS_APPLIED]] |
| frequency_cap | [[CAP_SEGMENT_DAILY_WEEKLY_COOLDOWN_OR_EXEMPT]] |
| flow_steps | [[FLOW_STEPS_SUMMARY]] |
| wait_times | [[WAIT_TIMES]] |
| branch_logic | [[BRANCH_CONDITIONS]] |
| email_purpose | [[EMAIL_PURPOSE]] |
| personalisation_fields | [[FIELDS_WITH_DEFAULTS]] |
| conversion_event | [[CONVERSION_EVENT]] |
| guardrail_metrics | [[GUARDRAIL_METRICS]] |
| compliance_notes | [[COMPLIANCE_NOTES]] |

Marketing (MKT, VIP): entry includes `SEG_CAN_RECEIVE_MARKETING`, exit includes
`SEG_RG_SUPPRESSED` and `RG_EXIT_BLOCK` (`templates/rg-exit-block.md`), topic is
a marketing topic, cap is numeric. RG, TXN, SVC, SYS: non-marketing topic, cap
`Exempt`. Trigger: one event (or a normalised event or segment trigger) and,
for segment triggers, the activation mode. Event exits count only events after
the trigger.

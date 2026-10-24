# RG_EXIT_BLOCK

Paste this block into the exit conditions of every marketing automation (every
MKT and VIP journey) and write `RG_EXIT_BLOCK` in the journey spec's
`exit_conditions` cell (validator rule C22). It is the second line of defence
after the entry gate and before the L4 pre-send check; it does not replace L4.

```text
RG_EXIT_BLOCK (exit when ANY is true; exit criteria are OR statements):
  attribute marketing_blocked is true
  attribute self_excluded is true
  attribute self_exclusion_register_match is true
  attribute timeout_active is true
  attribute rg_risk_level is one of high, severe
  attribute account_status is one of suspended, closed
  attribute aml_status is one of blocked, frozen, restricted
  attribute unsubscribed is true
  person is in segment SEG_RG_SUPPRESSED
```

Attribute conditions are listed first so the exit does not depend only on
segment recomputation; Customer.io publishes no recomputation SLA for segments
(verify before deployment).

Build notes:
- Configure it in the automation's exit settings as custom exit conditions;
  they may differ from the automation's goal.
- Bonus and VIP journeys add `rg_risk_level is not low` on top of the block.
- `marketing_blocked` is the operator kill switch (QA reference, Incident
  response); setting it exits everyone from marketing automations at once.
- Self-exclusion is recorded as attributes on the profile, never by deleting
  or suppressing the person (the never-suppress rule: SKILL.md hard rule 1;
  detail in the suppression gate reference).

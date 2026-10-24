# Protocol: design audit

Context: runs after intake when the user shares an existing CRM setup (export,
journey list, segment list or attribute schema) and wants it reviewed. A review
of the live Customer.io workspace pulled through the MCP is LIVE-AUDIT
(`protocols/live-audit.md`), which reuses steps 2-7 of this protocol.

## Mission
Report every gap between the setup and the libraries, ranked by player
protection first, with a concrete fix for each.

## Steps
1. Take the setup the user shared (export, lists, screenshots, schema) and
   record what it is in "Scope reviewed". If the user wants the live workspace
   pulled instead, switch to `protocols/live-audit.md`.
2. Inventory the setup into five lists: journeys (with trigger, activation,
   entry, exit, topic, limits, action conditions, waits), segments (with
   logic), attributes (with types and sync source), subscription topics, and
   frequency caps plus cap and counter settings. Note what the source does not
   show and ask for it, or record it as "not evidenced".
3. Compare in this order, reading each reference as you reach it:
   1. `references/suppression-gate.md`: the gate segment's conditions, L2 entry,
      L3 action conditions, L4 pre-send check, `RG_EXIT_BLOCK` on every
      marketing journey, no `suppress` use (SKILL.md hard rule 1), broadcast exclusion,
      reconciliation, audit log.
   2. `references/responsible-gambling.md`: signals, level actions, bonus
      suppression, VIP rules, timeout expiry handling.
   3. `references/segment-library.md`: data-driven only, exact logic, enums.
   4. `references/journey-catalogue.md`: missing journeys, wrong types or
      topics, multi-event triggers, Wait Until without Max time, activation
      mode on reactivation journeys.
   5. `references/subscription-topics.md`: topic assignment, mandatory topics,
      product x channel consent where `references/markets.json` requires it.
   6. `references/caps-and-priority.md`: frequency caps, cap table, counters,
      priority, conflicts.
   7. `references/platform-implementation.md`: naming, identify/track, webhooks.
   8. `references/qa-launch.md`: test evidence for the suppression cases.
4. Label each finding's Risk with exactly one value, using this rubric:
   - `player-protection`: any path where a self-excluded, timed-out, high or
     severe RG risk, underage or unverified-age, AML-restricted or unconsented
     player can receive marketing or a bonus; or an RG/SE message that can be
     suppressed or delayed.
   - `compliance`: a legal or licence obligation not met that does not reach a
     protected player directly (consent records, unlicensed-market send path,
     missing footer disclosures, transactional mail carrying offers, no audit log).
   - `revenue`: a missing or misbuilt lifecycle journey, segment or test that
     costs conversion or retention.
   - `hygiene`: naming, duplication, documentation, deliverability settings.
5. Fill `templates/audit-findings.md`. Sort rows player-protection, compliance,
   revenue, hygiene; inside each band, lowest effort first. Priority numbers
   run 1..n in that order.
6. Add the prioritised change list: one numbered action per finding or group of
   findings, each naming the exact segment condition, journey setting or
   attribute to change.
7. Stop condition: every inventory item was compared, every finding has a Risk
   label and a fix, and the table is sorted.

## Guidelines
- Pattern: quote the user's own condition next to the corrected one, so the fix
  is copy-paste ready.
- Pattern: one finding per defect. "Gate incomplete" hides three separate fixes.
- Anti-pattern: ranking by revenue first. A missing exit condition on a bonus
  journey outranks any conversion gain.
- Anti-pattern: auditing copy tone in depth. Flag loss-chasing or urgency risk
  as a compliance finding and move on; copywriting is out of scope.

## Next
Run `protocols/self-check.md` with `--mode audit`.

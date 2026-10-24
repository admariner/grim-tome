# Protocol: self-check

Context: runs after every DESIGN protocol and after LIVE-AUDIT, before
anything is delivered, and on the design a BUILD will use before BUILD stage 0.
It gates delivery on the mechanical checks, then applies the judgement the
script cannot. A BUILD's own output is checked by
`scripts/validate_build_sheet.py` (`protocols/build.md` stage 9).

## Mission
Deliver only a draft that passes `scripts/validate_crm_output.py` (or its
manual equivalent), survives the content judgement pass, and ends with the
canonical notice.

## Steps
1. Save the draft to a markdown file if it is not one already.
2. Run the validator from the skill folder:
   `python3 scripts/validate_crm_output.py DRAFT.md --mode <blueprint|flow|audit>`
   adding `--piece <journey|segments|gate|rg|caps>` for FLOW, `--markets "DE,SE"`
   with every intake market (market rules are read from
   `references/markets.json`; `--markets-file PATH` only for test data),
   `--operator "<name>"` when the user supplied the operator name,
   `--forbid "<name>"` for any client or source-operator name that must not
   appear, and `--events FILE` for mapped operator events.
3. Exit 1: fix every `[ERROR]` line at its `path:line`, then re-run until the
   exit code is 0. Review each `[WARN]`: fix or declare an unknown attribute or
   event; for C25 confirm the trigger; tell the user about every C27 (stale
   market row) and C28 (closed-pending market) warning in the delivery
   message. Exit 2: the command or the markets file is wrong; fix it and
   re-run. No code execution available: walk the manual checklist below,
   which mirrors the script one to one.
4. Judgement pass with the content rubric in `references/kpis-and-testing.md`:
   no loss-chasing framing, no false urgency or countdown pressure, nothing
   appealing to minors, no prohibited A/B category, wagering terms stated on
   every bonus email, no "increase your limit" message to limit-setters.
5. Confirm the four spec checks: every segment has exact conditions; every
   journey shows the gate (entry, per-send check, `RG_EXIT_BLOCK`) or the
   transactional gate; every intake market has its overlay; no placeholder
   text remains.
6. Make the last line of the deliverable exactly:
   "Legal/compliance review required: have qualified legal and compliance counsel review this design in every target jurisdiction before deployment."
7. Deliver per mode: BLUEPRINT as the markdown file (offer a document tool
   copy when the host has one); FLOW inline, or the file when long; design
   audit and LIVE-AUDIT findings table and change list inline. A design that
   feeds BUILD is delivered by moving on to `protocols/build.md`.

Manual checklist (same rules as the script, by rule ID):
- C01 no forbidden client names; C02 no bracketed to-be-decided markers, no
  `[[SLOT]]`, no "as appropriate", "insert ... here" or `<your ...>`; C03 all
  16 journey dimensions filled with real content (`-` and `n/a` do not count).
- C04 journey IDs `JRN_<TYPE>_NN_Name`, type matches; C05 segment IDs upper
  snake case, every logic has an operator.
- C06 marketing journeys: entry `SEG_CAN_RECEIVE_MARKETING`, exit
  `SEG_RG_SUPPRESSED`, marketing topic, numeric cap; C07 Gate column on every
  flow table, filled on every marketing Email row.
- C08 RG/TXN/SVC/SYS journeys: non-marketing topic, cap Exempt; C09 every
  offer Email row has Gate `BONUS`, and bonus journeys reference the bonus gate.
- C10 Liquid tags balanced, nested and in the Customer.io tag list, every
  output with a `default:` (warning; `countdown` warns); C11 fences closed,
  JSON parses.
- C12 17 sections in order (blueprint); C13 cap table zero rows and daily <=
  weekly; C14 priority levels 1-11 with RG_12 at 1; C15 the exact canonical
  notice (step 6) is one of the last 3 non-empty lines.
- C16 overlay block per market, with the verify marker (block and helpline
  line) when the markets.json row is not primary; C17/C18 attributes and
  events defined; C19 enum values valid; C20 gate lists all 14 conditions;
  C21 audit table shape.
- C22 every MKT/VIP exit has `RG_EXIT_BLOCK`; C23 every Wait Until has a
  fixed `max`; C24 no condition compares two attributes; C25 one trigger event
  (warning); C26 Bonus terms rows obey the market's `bonus_rules` and every
  bonus journey has a row; C27 market row older than 180 days (warning);
  C28 closed-pending market (warning) with its MARKET STATUS banner in the
  first 20 lines (error if missing); C29 every Liquid output in a TXN, SVC,
  SYS or RG journey has a `default:`.

## Guidelines
- Pattern: fix the source of a repeated error (a template slot, a copied
  journey) rather than patching each occurrence.
- Anti-pattern: adding words to satisfy a check without meaning them, such as
  a Gate cell that says "MKT" on a row the gate does not cover.
- Anti-pattern: delivering with warnings unread. A warning is a name the
  validator could not trace; trace it or declare it.

## Next
Deliver, or continue with `protocols/build.md` when this design feeds a BUILD;
run `protocols/self-refine.md` at the end of the session.

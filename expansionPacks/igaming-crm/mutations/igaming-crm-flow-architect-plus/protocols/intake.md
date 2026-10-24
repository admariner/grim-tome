# Protocol: intake

Context: runs after `protocols/intake-plus.md`, which asks the questions and
picks the mode. Steps 3-8 here turn the answers into design inputs; steps 1-2
apply when the user asked for DESIGN alone and intake-plus already ran.

## Mission
Know the markets, products, tiers, platform and licence posture, and know the
mode (and, for FLOW, the piece), before any design work starts.

## Steps
1. Extract what the request already answers. Do not ask for anything the user
   has stated or attached.
2. Ask only the missing items, using the merged question set in
   `protocols/intake-plus.md` (at most five questions; never a sixth). For a
   design audit of a shared export, question 5 becomes the export request:
   journey list with entry/exit conditions, segment definitions, attribute
   schema, subscription topics, frequency caps and cap settings.
3. If the user declines or says "use defaults", proceed and record each default
   as an explicit assumption line in the deliverable (for example "Assumption:
   offshore licence, no national register; internal self-exclusion database
   carries the full burden").
4. Map the licence type to the overlay baseline with the licence-posture table
   in `references/compliance-and-overlays.md`. For each market, look up its row
   in `references/markets.json` (market facts come only from that file); a
   market with no row needs assumptions plus questions from
   `references/legal-question-bank.md`. If a row's `market_status` is
   `closed_pending` (BR), tell the user now, in the intake summary, that the
   market is closed pending its status note and that counsel must confirm
   legal status before any send; then design its flows anyway and put the
   row's `banner` line at the top of the deliverable. Do not refuse and do not
   add a sixth question. Crypto
   payments add LQ_CRY_01 to LQ_CRY_03; esports adds LQ_MIX_01 to LQ_MIX_03.
   Unanswered questions follow the bank's rule: an explicit assumption flagged
   with the open question ID; only LQ_LIC_01 defaults to blocking marketing in
   that market.
5. Map operator event names onto the canonical events in
   `references/event-taxonomy.md` (keep a two-column mapping table). Names with
   no canonical match are kept as operator events and passed to the validator
   with `--events`.
6. Confirm the design sub-mode chosen at intake-plus: BLUEPRINT (full
   architecture), FLOW (one piece) or design audit (review of a shared
   export). For FLOW, name the piece: journey, segments,
   gate, rg or caps. A request for "a journey plus its segments" is FLOW
   journey; the journey piece already includes its segment logic.
7. Platform other than Customer.io: keep the architecture, plan to translate
   primitives with the primitive mapping table in
   `references/platform-implementation.md`, and add one line to the
   deliverable: "Platform translation is best effort from general platform
   knowledge; verify each primitive in the platform's documentation." Copy the
   table's "Verify in target platform" banner with it.
8. Stop condition: inputs and assumptions are written down, the mode (and
   piece) is chosen, and the mode protocol is open.

## Guidelines
- Pattern: one consolidated question message. Several rounds of single
  questions cost the user more than one short list.
- Pattern: offer the default inside the question ("Customer.io unless you use
  another platform?") so a one-word answer is enough.
- Anti-pattern: researching or drafting before the mode is known. Intake is
  short; the design waits for it.
- Anti-pattern: inventing a market's register, helpline or bonus rule. Unknown
  facts become assumptions and legal questions.

## Next
Open the mode protocol: `protocols/blueprint.md`, `protocols/flow.md`,
`protocols/design-audit.md`, `protocols/build.md` (after the design passes
self-check) or `protocols/live-audit.md`.

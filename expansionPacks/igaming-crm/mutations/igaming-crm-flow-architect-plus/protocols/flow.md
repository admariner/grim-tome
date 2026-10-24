# Protocol: flow

Context: runs after intake when the user wants one piece: a journey, a segment
set, the suppression gate, RG automation or a frequency-cap set.

## Mission
Deliver that one piece at implementation depth, consistent with the libraries,
adapted to the intake answers, and ready for the validator.

## Steps
1. Find the piece in the table below and read only its references.

   | Piece | References to read |
   |---|---|
   | journey | `references/journey-catalogue.md`, the matching `references/journey-flows-*.md` file, `references/suppression-gate.md`, `templates/rg-exit-block.md`, `references/subscription-topics.md`, `references/caps-and-priority.md`, `references/liquid-patterns.md`, `references/data-model.md`, `references/event-taxonomy.md`, plus `references/compliance-and-overlays.md` and `references/markets.json` when markets were named |
   | segments | `references/segment-library.md`, `references/data-model.md`, `references/event-taxonomy.md` |
   | gate | `references/suppression-gate.md`, `references/data-model.md`, `references/platform-implementation.md`, `references/qa-launch.md` |
   | rg | `references/responsible-gambling.md`, `references/journey-flows-protective.md`, `references/compliance-and-overlays.md`, `references/caps-and-priority.md` |
   | caps | `references/caps-and-priority.md`, `references/segment-library.md` |

   Matching flows file: TXN_01, SVC_02, MKT_03-05 in onboarding; MKT_06-10 and
   VIP_11 in engagement; RG_12 and SYS_13-15 in protective. A journey outside
   the catalogue starts from the closest catalogue entry and keeps its ID type.
2. Start from the library entry and adapt it to intake: products (topic and
   branch choices), tiers (VIP thresholds), markets (overlay branches), and the
   operator's event names (mapped, not renamed).
3. Journey deliverable: fill `templates/journey-spec.md` (all 16 dimensions:
   entry/exit conditions, suppression checks, subscription topic, frequency
   cap, branch logic, personalisation fields, conversion event, guardrail
   metrics, compliance notes) and `templates/flow-table.md` (Gate on every
   Email row, `BONUS` on every offer email). A MKT or VIP journey MUST write
   `RG_EXIT_BLOCK` in its exit cell and keep the pre-send webhook (L4); both
   are required. Every Wait Until carries a fixed `max`. A journey with more
   than one trigger event uses a normalised event or an attribute/segment
   trigger (platform implementation reference, "Triggers and activation"), and
   a segment-triggered reactivation or win-back journey states "Activation:
   only future additions". Add one Liquid block where personalisation
   branches, every variable with a `default:` fallback and operator constants
   from Snippets, and the pre-send webhook payload. A bonus journey with named
   markets adds the Bonus terms table from the market rows. Then walk the
   timing rule in `references/journey-catalogue.md` as a player who entered
   on day 0: every branch and email condition must be true when that player
   reaches it, event exits count only events after the trigger, and the
   journey must exit on the behaviour it is trying to cause, on every
   vertical. The validator cannot check this.
4. Segment deliverable: a table with columns Segment, Purpose, Logic, Journeys,
   Suppression, Priority, using the logic syntax of the segment library, and
   the Customer.io builder phrasing for any new segment.
5. Gate deliverable: canonical pseudocode, the L1-L4 configuration, the exit
   set, SLA budget, reconciliation and gate QA cases.
6. RG deliverable: signal table, level-action table, bonus suppression table,
   VIP rules, RG_12 spec and flow, spending summary contents.
7. Caps deliverable: the cap table (segment, daily, weekly, cooldown, bonus,
   cross-sell), evaluation order, counter mechanics and the most-restrictive rule.
8. Apply the overlay for every intake market from its `references/markets.json`
   row (a heading per market covering disclosures and helpline, register or
   suppression rule, RG requirement, with the verify marker on rows that are
   not primary). For a `closed_pending` market, put its `banner` line at the
   very top of the deliverable and still produce the flows.
9. Stop condition: the piece is complete, saved to a file if longer than about
   80 lines, and ends with the notice line.

## Guidelines
- Pattern: name the assumption next to the value it drives ("cap 1/2 per week,
  assuming the active_casual cap applies").
- Pattern: keep IDs in the canonical pattern (`JRN_MKT_09_Churn_Prevention`,
  `SEG_CHURN_RISK`) even when the operator's tool uses display names.
- Anti-pattern: a bonus step without `SEG_CAN_RECEIVE_BONUS` and a medium-risk
  exclusion. The bonus gate is part of the journey, not a later add-on.

## Next
Run `protocols/self-check.md` with `--mode flow --piece <piece>` and every intake
market in `--markets`.

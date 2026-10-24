# Protocol: blueprint

Context: runs after intake when the user wants the full CRM architecture for an
operator. It produces all 17 sections in canonical order, implementation-ready.

## Mission
Deliver one markdown file containing sections 1-17, the market overlays for
every intake market, and the legal/compliance notice, with names consistent
from the schema through the journeys.

## Steps
1. Copy `templates/blueprint-outline.md` to a working file named
   `<operator-or-project>-crm-blueprint.md`. Keep the 17 section titles exactly;
   the validator checks titles and order.
2. Write the sections in four batches. Before each batch, read only the
   references listed for it, and fill every `[[SLOT]]` in that batch.
   - Batch (a), sections 1-4: `references/data-model.md`,
     `references/event-taxonomy.md`, `references/segment-library.md`. Section 2
     includes at least every canonical attribute; section 3 every canonical
     event plus mapped operator events; section 4 every segment with exact logic.
   - Batch (b), sections 5-6: `references/suppression-gate.md`,
     `templates/rg-exit-block.md`, `references/subscription-topics.md`,
     `references/platform-implementation.md`. Section 5 carries the full gate
     pseudocode, the L1-L4 table and `RG_EXIT_BLOCK`.
   - Batch (c), sections 7-12: `references/journey-catalogue.md`,
     `references/journey-flows-onboarding.md`,
     `references/journey-flows-engagement.md`,
     `references/journey-flows-protective.md`, `references/liquid-patterns.md`,
     `references/responsible-gambling.md`, `references/caps-and-priority.md`.
   - Batch (d), sections 13-17: `references/kpis-and-testing.md`,
     `references/platform-implementation.md` (phases),
     `references/qa-launch.md`, `references/legal-question-bank.md`.
3. Sections 7 and 8: every one of the 15 journeys uses
   `templates/journey-spec.md` (all 16 dimensions) and `templates/flow-table.md`
   (Gate column filled on every Email row). Every MKT and VIP spec MUST carry
   `RG_EXIT_BLOCK` (`templates/rg-exit-block.md`) in its exit cell, one
   trigger event (or a normalised event or segment trigger) and a fixed `max`
   on every Wait Until. Adapt waits, topics and branches to the intake
   products; drop a journey only if the operator lacks the product, and say
   so in section 7.
4. Section 5: `RG_EXIT_BLOCK` and L4 are both required. If the operator has
   accepted the async quiet-period variant in writing, keep L4 documented and
   add the flagged accepted-risk block from `references/suppression-gate.md`.
   Without written acceptance, L4 is required.
5. Add `## Appendix A. Market Overlays` with one block per intake market, built
   from the overlay template and its `references/markets.json` row as
   `references/compliance-and-overlays.md` describes, plus a Bonus terms table
   for bonus journeys. A `closed_pending` market's `banner` goes on the first
   line of the file. Markets without a row get stated assumptions and their
   legal question IDs.
6. Consistency pass: every attribute, enum value, event and segment used in
   sections 4-12 appears in sections 2-4. Fix the use or add the definition.
7. Save the file. Always deliver it as a markdown file; if the host offers a
   document tool, also offer to publish the same content there.
8. Stop condition: the file holds 17 sections, Appendix A and a final notice
   line, with no `[[SLOT]]` left.

## Guidelines
- Pattern: write section 4 before section 7, so journeys reference segments
  that already exist rather than names invented on the fly.
- Pattern: keep section prose short; tables and code blocks carry the design.
- Anti-pattern: copying the reference journeys unchanged when the operator has
  no sportsbook or no VIP programme. Adapt topics, branches and caps.
- Anti-pattern: email copy, HTML templates or brand voice. Section 9 is a
  content matrix (purpose, offer type, RG requirement), not copy.

## Next
Run `protocols/self-check.md` with `--mode blueprint` and every intake market in
`--markets`.

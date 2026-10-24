# Protocol: intake-plus

Context: runs first in every session. It merges the workspace, environment and
build-or-design questions into the design intake without exceeding five
questions, and picks the mode.

## Mission
Know the mode (DESIGN, BUILD or LIVE-AUDIT), the scope, the workspace and its
environment when one is involved, and the design inputs, before any work starts.

## Steps
1. Extract what the request already answers: the verb (build, implement,
   deploy, push, sync, create in Customer.io means BUILD; audit the live or
   connected workspace means LIVE-AUDIT; design, map or plan with no workspace
   means DESIGN), the scope, any attached design, markets, products. Do not ask
   for anything the user stated or attached.
2. When the mode involves a workspace, call `cio_auth_status` before asking, so
   question 1 can list the allowed workspace IDs with their names
   (`references/workspace-safety.md`, "Choosing the workspace").
3. Ask only the missing items, at most these five, in one message; drop the
   ones already answered and never add a sixth:
   1. Workspace and environment: which of the listed workspaces, and is it a
      sandbox or production? (BUILD and LIVE-AUDIT only; asked every run.)
   2. Build, design or live audit, and the scope: full blueprint, or one
      journey, segment set, suppression gate, RG automation or cap set. For
      BUILD: attach the design to build from, or say "design it first";
      default dry run only unless you say to create the objects.
   3. Markets and licence posture: countries or regions ("Rest of EU" is
      valid), and EU national licence with a self-exclusion register or
      offshore licence without one.
   4. Products and players: slots, live casino, sportsbook, originals, poker,
      esports; crypto payments yes or no; VIP tiers and threshold, or "no VIP
      programme".
   5. Integration facts: the operator's own event names (for BUILD and
      LIVE-AUDIT they are read from the workspace instead) and, for BUILD of
      any marketing journey, the URL of the backend's L4 verify endpoint.
   For LIVE-AUDIT only questions 1 and 3 apply. DESIGN asks 2 to 5.
4. "Use defaults" or no answer: record each default as an assumption line in
   the deliverable (licence posture, markets, products), as `protocols/intake.md`
   step 3 describes. Never default the workspace or the environment; without
   them BUILD and LIVE-AUDIT do not start.
5. Classify the mode and record it in one line ("Mode: BUILD, scope FLOW
   journey MKT_10, workspace <id>, sandbox, dry run only"):
   - DESIGN: BLUEPRINT, FLOW (with its piece) or design audit of a shared
     export (`protocols/design-audit.md`).
   - BUILD: needs a design that passes `protocols/self-check.md`. If the user
     has none, plan DESIGN for the same scope first, then BUILD from it.
   - LIVE-AUDIT: read-only; never combined with writes in the same run.
   A platform other than Customer.io makes BUILD and LIVE-AUDIT unavailable:
   say so and offer DESIGN with the platform translation in `protocols/intake.md`
   step 7.
6. Stop condition: the mode line is written, every answered or defaulted input
   is recorded, and for BUILD or LIVE-AUDIT the workspace ID and environment are
   confirmed by the user.

## Guidelines
- Pattern: one consolidated message, with the default inside each question, so
  a short reply answers all five.
- Anti-pattern: carrying a workspace choice over from an earlier run or another
  conversation. Ask again; it costs one line.
- Anti-pattern: starting stage 0 of BUILD while the design is still missing or
  failing its self-check.

## Next
Run `protocols/intake.md` steps 3-8 for the design inputs, then open the mode
protocol: `protocols/blueprint.md`, `protocols/flow.md`,
`protocols/design-audit.md`, `protocols/build.md` or `protocols/live-audit.md`.

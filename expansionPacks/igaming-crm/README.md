# iGaming CRM Expansion Pack (Beta)

One first-party skill by admariner, authored and synced as a claude.ai account skill and seated here as a beta expansion pack. MIT licensed; the license ships beside this file as [`LICENSE`](LICENSE). Source: the claude.ai account skill `igaming-crm-flow-architect-plus` v1.2.0 (no public URL). That account copy is the source of truth.

`/igaming-crm-flow-architect-plus` designs player-lifecycle CRM for casino and sportsbook operators and builds it in Customer.io through the official Customer.io MCP: suppression gate, segments, subscription topics, frequency caps, webhooks and journeys, in a fixed, dependency-ordered, idempotent build.

| Mode | What it does |
|---|---|
| DESIGN | Blueprint, one journey, segment set, gate, RG automation or cap set, or a review of a shared export. Works without a workspace. |
| BUILD | Creates the design's objects in a chosen workspace, stage by stage, each stage previewed with `dry_run` and run only on approval. Every automation stays in draft with responsible-gambling exits. Ends with a build sheet, rollback list, smoke report and activation checklist. |
| SMOKE | Proves the gate and the draft journeys sort test players correctly, with parked `smk-` synthetic profiles. Nothing started or sent. |
| LIVE-AUDIT | Read-only review of a live workspace: a findings ledger (Configuration audit and Data exploration) with owners, fixes and verify checks. Nothing written. |

**Safety:** the skill never activates, starts or schedules an automation, never sends anything, and never deletes people or objects. Activation and deletion stay with you. The only people it writes are its own `smk-` smoke profiles, after a dry run and your approval.

### Naming and lifecycle

- The skill keeps its **upstream invocation name** (`invocation: upstream`), so `/igaming-crm-flow-architect-plus` works the same here and on claude.ai.
- It is **beta**: manual-only (`disable-model-invocation: true`, `allow_implicit_invocation: false`), and `lifecycle: beta` in `pack.yaml` and the skill's frontmatter metadata. Right for a skill that writes to a live workspace.
- It is a light mutation (`mutation: true`). The unmodified account `SKILL.md` lives at `mutations/igaming-crm-flow-architect-plus/original/UPSTREAM.md`; protocols, references, templates, scripts and fixtures are unmodified copies.
- The pack sits outside `skills/registry.yaml`, so it is not bundled into the `grim-tome` plugin and does not sit as a second same-name copy next to the synced account skill.

### What changed vs the account copy

- **Frontmatter:** added `disable-model-invocation`, `mutation`, `source_url`, `original_skill`, and `author`, `pack`, `lifecycle` under `metadata`.
- **`agents/openai.yaml`:** added, with implicit invocation off. No icons while in beta.
- **`CHANGELOG.md`** replaces the account copy's refinement log: one short entry per version, with no workspace observations or internal notes. The pointers in `SKILL.md` and `protocols/self-refine.md` follow it.
- **`protocols/self-refine.md` step 4:** a third case, "Tome repo copy": change the pack, add a changelog line, and hand the same change to the account skill so the copies do not drift.

Nothing else in the skill body changes. It is a responsible-gambling compliance skill; its text stays plain.

### Syncing updates

- **Account to Tome:** diff `original/UPSTREAM.md` against the new account `SKILL.md`, copy the rest of the skill over, re-apply the changes above, refresh `UPSTREAM.md`, and add a `CHANGELOG.md` entry (no workspace or client detail).
- **Tome to account:** a change made here goes to the account skill through the skill-proposal flow, per `protocols/self-refine.md` step 4.
- Run the validator commands in `protocols/self-refine.md` step 5 from the skill root after either direction.

### Requirements

- The official Customer.io MCP server (`cio_*` tools) for BUILD, SMOKE and LIVE-AUDIT. DESIGN works without it.
- Python 3.8+, standard library only, for `scripts/validate_crm_output.py` and `scripts/validate_build_sheet.py`.

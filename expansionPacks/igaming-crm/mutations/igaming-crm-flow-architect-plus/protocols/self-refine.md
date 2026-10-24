# Protocol: self-refine

Context: skills decay unless they learn from use. Run this at the end of a
session that exercised this skill.

## Mission
Improve this skill for next time using evidence from this session and user
feedback, and record the change.

## Steps
1. Review the session: what went smoothly, and where using this skill hit
   friction (a missing reference fact, a validator false positive, an intake
   question the user could not answer, a journey that needed heavy rework, a
   Customer.io call refused or a mechanic marked "(verify in workspace)" now
   confirmed or contradicted, which goes into `references/build-order.md`).
2. Ask the user for one concrete piece of feedback if any is available. Their
   correction outranks your own read of the session.
3. Pick the single smallest change that prevents the top friction from
   recurring. Favour sharpening an existing file over adding a new one.
4. Check whether the skill folder is writable (Claude Code install: yes; a skill
   uploaded to claude.ai: read-only).
   - Writable: apply the change to the right file (router, reference,
     protocol, template or script) and add an entry at the top of
     `CHANGELOG.md` in the skill root: date, change, files.
     (All paths in this protocol are relative to the skill root.)
   - Read-only: do not attempt the edit. Give the user the proposed change as
     an exact before/after snippet with its file path, plus the log line to
     append, so they can apply it at the source copy and re-upload.
   - Tome repo copy (the `igaming-crm` expansion pack): apply the change in the
     pack, add a `CHANGELOG.md` line with no workspace or client detail, and
     hand the same change to the claude.ai account skill through the skill
     proposal flow so the two copies do not drift. The claude.ai account skill
     is the source of truth.
5. Writable case: from the skill root, re-run
   `python3 scripts/validate_crm_output.py` with
   `--mode flow --piece journey --forbid "Northwind Casino"` plus:
   `scripts/fixtures/good.md --markets DE` (expect exit 0),
   `scripts/fixtures/bad.md --markets DE` (expect exit 1),
   `scripts/fixtures/good-markets.md --markets UK,BR` (expect exit 0 with a
   C28 warning), `scripts/fixtures/bad-markets.md --markets UK,SE,BR` (expect
   exit 1), `scripts/fixtures/bad-markets.md --markets Brazil` (expect exit 1
   with the C28 banner error: full names resolve to codes),
   `scripts/fixtures/good.md --markets "Germany,LatAm"` (expect exit 1 with a
   C16 "no market row" warning for LatAm), and `scripts/fixtures/good.md
   --markets DE --markets-file scripts/fixtures/markets-stale.json` (expect
   exit 0 with a C27 warning); and with `--mode audit` alone:
   `scripts/fixtures/good-live-audit.md` (expect exit 0) and
   `scripts/fixtures/bad-live-audit.md` (expect exit 1 with C30 errors), so
   the change does not regress the validator.
   Then run `python3 scripts/validate_build_sheet.py` on
   `scripts/fixtures/good-build-sheet.md` and
   `scripts/fixtures/good-created-build-sheet.md` (expect exit 0),
   `scripts/fixtures/stopped-build-sheet.md` (expect exit 0 with a B01
   warning), `scripts/fixtures/empty-build-sheet.md` and
   `scripts/fixtures/bad-build-sheet.md` (expect exit 1) and a path that does
   not exist (expect exit 2).
6. Writable case: repackage if this skill ships as an artifact; a refinement
   left unpackaged is a refinement the user never receives.

## Guidelines
- Pattern: one evidence-backed fix per session beats a speculative rewrite. The
  log should read as a history of real problems solved.
- Pattern: when the user gives feedback, encode it in a file or a check so it
  holds without them repeating it.
- Anti-pattern: refining in the abstract. If nothing went wrong and the user has
  no feedback, log "no change" (or tell the user so on a read-only install) and
  stop.
- Anti-pattern: growing the router during refinement. New detail goes in a folder.

## Next
This is the terminal protocol for a session. Report the change (or the proposed
change, on a read-only install) and the log entry to the user.

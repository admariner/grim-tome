#!/usr/bin/env python3
"""Validate a BUILD sheet written by protocols/build.md (templates/build-sheet.md).

Mechanical checks that make a build reviewable and re-runnable:
  B01 the Objects table exists with the required columns          ERROR
      no rows: WARN when the sheet records "Stopped at stage N:",
      ERROR otherwise
  B02 every row has spec ID, type, Customer.io ID, result, state  ERROR
  B03 type is a known object type; no delete rows or results      ERROR
  B04 spec ID prefix and shape match the type (SEG_, JRN_, ...)   ERROR
  B05 the name carries the spec ID (topics: Notes; snippets: the
      Liquid name equals the spec ID without SNP_; message
      actions: the name starts with the step)                     ERROR
  B06 Customer.io ID is an integer, or dry-run on a planned row   ERROR
  B07 automation state is draft, paused or stopped; message
      action state is draft; reporting webhook state is disabled  ERROR
  B08 MKT_/VIP_ automations list RG_EXIT_BLOCK (or its four core
      attributes) and SEG_RG_SUPPRESSED, a marketing topic and a
      LIM_ frequency cap; each of their message actions names a
      marketing topic                                             ERROR
      a MKT_/VIP_ automation with no message action rows          WARN
  B09 RG/TXN/SVC/SYS automations and their message actions: non-
      marketing topic; automations use no frequency cap           ERROR
  B10 topics, caps, segments and parent automations a row names
      exist as rows                                               ERROR
  B11 no duplicate spec IDs (a re-run must reuse, not duplicate)  ERROR
  B12 no unfilled template slots or to-be-decided markers         ERROR
  B13 Workspace line and activation checklist present             WARN
  B14 a rollback list (in the sheet under "Rollback list", or the
      --rollback file) names every created row except message
      actions, which go with their automation                     ERROR
  B15 each "Pre-flight:" line (build stage 0b) reads
      "Pre-flight: stage N GO|NO-GO: reason"                      WARN
  B16 a sheet that names SMOKE-REPORT.md has that file beside it  WARN

Output: one line per finding, "FILE:LINE: Bnn [ERROR|WARN] message", then a
tally. Exit 0 when there is no ERROR (warnings allowed), 1 when there is at
least one ERROR, 2 on a usage problem (missing or unreadable file, no Objects
table at all). Stdlib only, Python 3.8+.

Usage:
  python3 scripts/validate_build_sheet.py BUILD-SHEET.md
  python3 scripts/validate_build_sheet.py BUILD-SHEET.md --rollback ROLLBACK.md
  python3 scripts/validate_build_sheet.py BUILD-SHEET.md --json
"""
import argparse
import json
import os
import re
import sys

REQUIRED_COLUMNS = ["stage", "spec id", "type", "name", "customer.io id",
                    "result", "state", "topic", "limit", "exit conditions",
                    "notes"]

# Spec ID prefix per object type (references/object-naming.md).
TYPE_PREFIX = {
    "subscription_topic": "TOP_",
    "snippet": "SNP_",
    "segment": "SEG_",
    "frequency_cap": "LIM_",
    "webhook_configuration": "WHK_",
    "reporting_webhook": "WHK_",
    "automation": "JRN_",
    "message_action": "JRN_",
}
RESULTS = {"created", "existing", "planned"}
AUTOMATION_STATES = {"draft", "paused", "stopped"}
MARKETING_TOPICS = {"TOP_CASINO_OFFERS", "TOP_SPORTSBOOK_OFFERS",
                    "TOP_VIP_LOYALTY", "TOP_PRODUCT_UPDATES"}
SERVICE_TOPICS = {"TOP_SAFER_GAMBLING", "TOP_TRANSACTIONAL"}
# The four attributes that make an exit set an RG exit even when the sheet
# lists conditions instead of the block name (same rule as validator C22).
RG_CORE = ["self_excluded", "self_exclusion_register_match", "timeout_active",
           "rg_risk_level"]
NO_LIMIT = {"none", "-", "exempt", "no limit"}
# Unfilled slots and to-be-decided markers; the character classes keep the
# markers themselves out of this file.
PLACEHOLDER = re.compile(r"\[\[|\bT[O]DO\b|\bT[B]D\b|\[ins[e]rt", re.IGNORECASE)
JRN = re.compile(r"^JRN_(MKT|VIP|RG|TXN|SVC|SYS)_\d{2}_[A-Za-z0-9_]+$")
# Message action: <journey spec ID>#<step>[.<sub>][-<variant>]
MSG = re.compile(r"^(JRN_(MKT|VIP|RG|TXN|SVC|SYS)_\d{2}_[A-Za-z0-9_]+)"
                 r"#(\d+(?:\.\d+)?(?:-[a-z0-9_]+)?)$")
# A documented stop written by protocols/build.md ("Stopped at stage N: ...").
STOPPED = re.compile(r"\bstopped at stage (\d+)\b", re.IGNORECASE)
ROLLBACK_HEADING = re.compile(r"^#+\s*Rollback list", re.IGNORECASE)
# Readiness pre-flight lines written at build stage 0b.
PREFLIGHT_LINE = re.compile(r"^\s*Pre-flight:", re.IGNORECASE)
PREFLIGHT_OK = re.compile(r"^\s*Pre-flight:\s*stage\s+\d+b?\s+(GO|NO-GO)\s*:\s*\S",
                          re.IGNORECASE)
SMOKE_FILE = "SMOKE-REPORT.md"


class Report:
    def __init__(self, path):
        self.path = path
        self.items = []

    def add(self, level, line, rule, msg):
        self.items.append({"file": self.path, "line": line, "rule": rule,
                           "level": level, "message": msg})

    def error(self, line, rule, msg):
        self.add("ERROR", line, rule, msg)

    def warn(self, line, rule, msg):
        self.add("WARN", line, rule, msg)

    @property
    def errors(self):
        return [i for i in self.items if i["level"] == "ERROR"]


def split_row(line):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def find_table(lines, start=0, need=("spec id", "type", "customer.io id")):
    """Return (header_line_no, column index map, [(line_no, cells)]) for the
    first table at or after `start` whose header holds every column in `need`."""
    for i in range(start, len(lines)):
        line = lines[i]
        if not line.strip().startswith("|"):
            continue
        cols = [c.lower() for c in split_row(line)]
        if all(n in cols for n in need):
            index = {c: n for n, c in enumerate(cols)}
            rows = []
            j = i + 1
            if j < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[j]):
                j += 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append((j + 1, split_row(lines[j])))
                j += 1
            return i + 1, index, rows
    return None, None, None


def cell(cells, index, name):
    n = index.get(name)
    if n is None or n >= len(cells):
        return ""
    return cells[n].strip().strip("`")


def rollback_specs(lines):
    """Spec IDs listed in the table under a 'Rollback list' heading, or None."""
    for i, line in enumerate(lines):
        if ROLLBACK_HEADING.match(line):
            header, index, rows = find_table(lines, i, need=("spec id",))
            if header is None:
                return set()
            return {cell(c, index, "spec id") for _, c in rows}
    return None


def check_row(rep, ln, cells, index, by_spec, seen, msg_parents):
    spec = cell(cells, index, "spec id")
    typ = cell(cells, index, "type").lower()
    name = cell(cells, index, "name")
    cid = cell(cells, index, "customer.io id")
    result = cell(cells, index, "result").lower()
    state = cell(cells, index, "state").lower()
    topic = cell(cells, index, "topic")
    limit = cell(cells, index, "limit")
    exits = cell(cells, index, "exit conditions")
    notes = cell(cells, index, "notes")

    for label, value in (("spec ID", spec), ("type", typ),
                         ("Customer.io ID", cid), ("result", result),
                         ("state", state)):
        if not value or value == "-":
            rep.error(ln, "B02", "row %s has no %s" % (spec or "?", label))

    if "delete" in typ or "delete" in result or "delete" in state:
        rep.error(ln, "B03", "%s: delete is never part of a build; removal "
                  "belongs in the rollback list for the user" % spec)
        return
    if typ and typ not in TYPE_PREFIX:
        rep.error(ln, "B03", "%s: unknown type '%s'; use one of %s"
                  % (spec, typ, ", ".join(sorted(TYPE_PREFIX))))
        return
    if result and result not in RESULTS:
        rep.error(ln, "B02", "%s: result '%s' is not one of %s"
                  % (spec, result, ", ".join(sorted(RESULTS))))

    if spec in seen:
        rep.error(ln, "B11", "%s appears twice (first on line %d); a "
                  "re-run must find and reuse the object" % (spec, seen[spec]))
    else:
        seen[spec] = ln

    prefix = TYPE_PREFIX.get(typ, "")
    if spec and prefix and not spec.startswith(prefix):
        rep.error(ln, "B04", "%s: %s spec IDs start with %s" % (spec, typ, prefix))

    if cid and not re.match(r"^\d+$", cid):
        if cid.lower() == "dry-run":
            if result != "planned":
                rep.error(ln, "B06", "%s: Customer.io ID dry-run needs result "
                          "planned" % spec)
        elif cid != "-":
            rep.error(ln, "B06", "%s: Customer.io ID '%s' is not an integer"
                      % (spec, cid))

    if typ == "subscription_topic":
        if spec and spec not in notes:
            rep.error(ln, "B05", "%s: topic description must carry the spec ID; "
                      "write 'description: %s' in Notes" % (spec, spec))
    elif typ == "snippet":
        if spec.startswith("SNP_") and name != spec[4:].lower():
            rep.error(ln, "B05", "%s: snippet name should be '%s'"
                      % (spec, spec[4:].lower()))
    elif typ != "message_action" and spec and spec not in name:
        rep.error(ln, "B05", "%s: name '%s' does not carry the spec ID"
                  % (spec, name))

    if typ == "reporting_webhook" and state and state != "disabled":
        rep.error(ln, "B07", "%s: reporting webhook state '%s'; the build creates "
                  "it disabled and the user enables it" % (spec, state))

    topics = set(re.findall(r"\bTOP_[A-Z0-9_]+\b", topic))
    limits = set(re.findall(r"\bLIM_[A-Z0-9_]+\b", limit))
    refs = set(topics)

    if typ == "message_action":
        m = MSG.match(spec)
        if not m:
            rep.error(ln, "B04", "%s: message action spec ID must be "
                      "<journey spec ID>#<step>[-<variant>]" % spec)
            return
        parent, jtype, step = m.group(1), m.group(2), m.group(3)
        msg_parents.add(parent)
        refs.add(parent)
        if not name.startswith(step + " "):
            rep.error(ln, "B05", "%s: message action name must start with its "
                      "step '%s ' (object-naming reference)" % (spec, step))
        if state and state != "draft":
            rep.error(ln, "B07", "%s: message action sending_state '%s'; the build "
                      "creates every message action in draft" % (spec, state))
        if jtype in ("MKT", "VIP"):
            if not topics & MARKETING_TOPICS:
                rep.error(ln, "B08", "%s: marketing message action needs its own "
                          "marketing topic (%s)" % (spec, ", ".join(sorted(MARKETING_TOPICS))))
        elif not topics & SERVICE_TOPICS:
            rep.error(ln, "B09", "%s: %s message action needs a non-marketing topic "
                      "(%s)" % (spec, jtype, ", ".join(sorted(SERVICE_TOPICS))))
    elif typ == "automation":
        if state and state not in AUTOMATION_STATES:
            rep.error(ln, "B07", "%s: automation state '%s'; the build never "
                      "starts automations (allowed: %s)"
                      % (spec, state, ", ".join(sorted(AUTOMATION_STATES))))
        m = JRN.match(spec)
        if not m:
            rep.error(ln, "B04", "%s: journey spec ID must match "
                      "JRN_<TYPE>_<NN>_<Name>" % spec)
            return
        jtype = m.group(1)
        refs |= limits | set(re.findall(r"\bSEG_[A-Z0-9_]+\b", exits))
        if jtype in ("MKT", "VIP"):
            if not ("RG_EXIT_BLOCK" in exits or all(a in exits for a in RG_CORE)):
                rep.error(ln, "B08", "%s: marketing automation without the RG exit "
                          "conditions (RG_EXIT_BLOCK)" % spec)
            if "SEG_RG_SUPPRESSED" not in exits:
                rep.error(ln, "B08", "%s: RG exits must include SEG_RG_SUPPRESSED "
                          "with its ID" % spec)
            if not topics & MARKETING_TOPICS:
                rep.error(ln, "B08", "%s: marketing automation needs a default "
                          "marketing topic (%s)" % (spec, ", ".join(sorted(MARKETING_TOPICS))))
            if not limits:
                rep.error(ln, "B08", "%s: marketing automation needs a LIM_ "
                          "frequency cap opt-in" % spec)
        else:
            if not topics & SERVICE_TOPICS:
                rep.error(ln, "B09", "%s: %s automation needs a non-marketing topic "
                          "(%s)" % (spec, jtype, ", ".join(sorted(SERVICE_TOPICS))))
            if limits or limit.lower() not in NO_LIMIT:
                rep.error(ln, "B09", "%s: %s automation must not use a frequency "
                          "cap (write 'none')" % (spec, jtype))
    else:
        return

    for ref in sorted(refs):
        if ref not in by_spec:
            rep.error(ln, "B10", "%s references %s, which has no row in the sheet; "
                      "add it as created, existing or planned" % (spec, ref))


def check(path, text, rollback_text=None):
    rep = Report(path)
    lines = text.splitlines()

    for n, line in enumerate(lines, 1):
        if PLACEHOLDER.search(line):
            rep.error(n, "B12", "unfilled slot or to-be-decided marker: '%s'"
                      % line.strip()[:70])

    header, index, rows = find_table(lines)
    if header is None:
        return rep, False
    missing = [c for c in REQUIRED_COLUMNS if c not in index]
    if missing:
        rep.error(header, "B01", "Objects table lacks column(s): %s (template: "
                  "templates/build-sheet.md)" % ", ".join(missing))
        return rep, True

    stop = STOPPED.search(text)
    if not rows:
        if stop:
            rep.warn(header, "B01", "Objects table has no rows; the sheet records "
                     "a stop at stage %s, so nothing was built. Re-run BUILD after "
                     "the stop reason is fixed" % stop.group(1))
        else:
            rep.error(header, "B01", "Objects table has no rows. Add one row per "
                      "object, or, if a stage stopped the build, write 'Stopped at "
                      "stage N: <reason>' and list the objects under 'Not built'")
    else:
        by_spec = {}
        for ln, cells in rows:
            spec = cell(cells, index, "spec id")
            if spec:
                by_spec.setdefault(spec, ln)
        seen, msg_parents = {}, set()
        for ln, cells in rows:
            check_row(rep, ln, cells, index, by_spec, seen, msg_parents)

        for ln, cells in rows:
            spec = cell(cells, index, "spec id")
            if (cell(cells, index, "type").lower() == "automation"
                    and re.match(r"^JRN_(MKT|VIP)_", spec) and spec not in msg_parents):
                rep.warn(ln, "B08", "%s: no message_action rows; list each email "
                         "with its own topic so per-message topics can be checked"
                         % spec)

        created = [(ln, cell(c, index, "spec id")) for ln, c in rows
                   if cell(c, index, "result").lower() == "created"
                   and cell(c, index, "type").lower() != "message_action"]
        if created:
            listed = rollback_specs(rollback_text.splitlines()) if rollback_text \
                else rollback_specs(lines)
            if listed is None:
                rep.error(created[0][0], "B14", "created objects but no rollback "
                          "list; add a '# Rollback list' section from "
                          "templates/rollback-list.md or pass --rollback FILE")
            else:
                for ln, spec in created:
                    if spec not in listed:
                        rep.error(ln, "B14", "%s was created but is not on the "
                                  "rollback list" % spec)

    for n, line in enumerate(lines, 1):
        if PREFLIGHT_LINE.match(line) and not PREFLIGHT_OK.match(line):
            rep.warn(n, "B15", "pre-flight line should read 'Pre-flight: stage N "
                     "GO|NO-GO: <reason>' (protocols/build.md stage 0b)")

    if SMOKE_FILE in text:
        smoke_path = os.path.join(os.path.dirname(os.path.abspath(path)), SMOKE_FILE)
        if not os.path.isfile(smoke_path):
            rep.warn(1, "B16", "the sheet names %s but no such file is beside it; "
                     "write the smoke report (protocols/smoke.md S8) or record the "
                     "reason for skipping" % SMOKE_FILE)

    if not re.search(r"^Workspace:\s*\S", text, re.MULTILINE):
        rep.warn(1, "B13", "no 'Workspace:' line; the sheet must say which "
                 "workspace it describes")
    if not re.search(r"^#+\s*Activation checklist", text, re.MULTILINE | re.IGNORECASE):
        rep.warn(1, "B13", "no Activation checklist section; activation is the "
                 "user's and needs its list")
    return rep, True


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sheet", help="build sheet markdown file")
    ap.add_argument("--rollback", help="rollback list file, when it is not inside the sheet")
    ap.add_argument("--json", action="store_true", help="print findings as JSON")
    args = ap.parse_args(argv)
    try:
        text = read(args.sheet)
        rollback_text = read(args.rollback) if args.rollback else None
    except FileNotFoundError as exc:
        print("error: file not found: %s (pass the build sheet written in "
              "protocols/build.md stage 9)" % exc.filename, file=sys.stderr)
        return 2
    except OSError as exc:
        print("error: cannot read: %s" % exc, file=sys.stderr)
        return 2
    rep, has_table = check(args.sheet, text, rollback_text)
    if not has_table:
        print("error: %s has no Objects table with columns Spec ID, Type and "
              "Customer.io ID (template: templates/build-sheet.md)" % args.sheet,
              file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(rep.items, indent=2))
    else:
        for i in rep.items:
            print("%s:%d: %s [%s] %s" % (i["file"], i["line"], i["rule"],
                                         i["level"], i["message"]))
        n_err = len(rep.errors)
        print("%d error(s), %d warning(s)" % (n_err, len(rep.items) - n_err))
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())

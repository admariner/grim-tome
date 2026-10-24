#!/usr/bin/env python3
"""Validate an igaming-crm-flow-architect deliverable (BLUEPRINT, FLOW or AUDIT).

Mechanical checks on the skill's own outputs, so the rules a reviewer would
otherwise eyeball (gate on every marketing send, no placeholders, balanced
Liquid, 17 sections, cap-table invariants, valid enums) are enforced by code.
Judgement rules (loss-chasing, false urgency, appeal to minors) are NOT here:
they live in references/kpis-and-testing.md and are applied by the model.

Rules (level, scope):
  C01 forbidden names (--forbid), the --operator name exempt     ERROR all
  C02 placeholders and unfilled template slots                  ERROR all
  C03 journey spec tables complete (16 dimensions, not - or n/a) ERROR blueprint, flow/journey
  C04 journey ID format and type prefix                          ERROR blueprint, flow/journey
  C05 segment ID format; segment logic contains an operator      ERROR blueprint, flow/segments, flow/journey
  C06 marketing journeys gated (entry, exit, topic, cap)         ERROR blueprint, flow/journey
  C07 Gate column on flow tables; gate on marketing Email rows   ERROR blueprint, flow/journey
  C08 RG/TXN/SVC/SYS journeys: non-marketing topic, cap Exempt   ERROR blueprint, flow/journey
  C09 offer Email rows carry Gate BONUS; bonus journeys gated    ERROR blueprint, flow/journey
  C10 Liquid balanced, nested, official tag list only            ERROR all
      Liquid output without a | default: fallback                WARN  all
      countdown tag (check the false-urgency rubric)             WARN  all
  C11 code fences closed; json fences parse                      ERROR all
  C12 17 canonical sections in order                             ERROR blueprint
  C13 cap table values and zero rows                             ERROR blueprint, flow/caps (required); else if present
  C14 priority table levels 1-11, RG_12 at level 1               ERROR blueprint
  C15 canonical legal/compliance notice in the last 3 lines      ERROR all
  C16 overlay block for each --markets value; marker on rows     ERROR when --markets given
      that are not primary (block and helpline line); full names
      (Brazil, United Kingdom) resolve to codes; a market with no
      markets.json row                                           WARN  (C26-C28 not evaluated)
  C17 attributes in conditions are defined                       WARN  all
  C18 trigger and conversion events are defined                  WARN  blueprint, flow/journey
  C19 enum values valid for enum attributes                      ERROR all
  C20 gate lists all fourteen conditions                         ERROR blueprint, flow/gate
  C21 audit findings table shape, risk enum, sort order          ERROR audit
  C22 MKT/VIP exit includes RG_EXIT_BLOCK (or its four core      ERROR blueprint, flow/journey
      attributes)
  C23 every Wait Until has a fixed Max time (max N h|d)          ERROR all
  C24 no condition compares two attributes                       ERROR all
  C25 trigger names one event (or a normalised/attribute/        WARN  blueprint, flow/journey
      segment trigger)
  C26 Bonus terms table obeys each market's bonus_rules          ERROR when --markets has bonus rules
      (markets.json: max wagering, single product, first play,
      deposit-conditional)
  C27 market row verified_on older than stale_after_days         WARN  when --markets given
  C28 closed_pending market: warning, plus the MARKET STATUS     WARN; banner missing ERROR
      banner line near the top
  C29 Liquid output without | default: in a TXN/SVC/SYS/RG       ERROR all
      journey (elsewhere the C10 warning)
  C30 live-audit ledger (a findings table with an Owner column,  ERROR audit
      or "### P<n>" / "### X<n>" finding blocks): Priority cell is
      a P<n>/X<n> label, one prefix per table, labels unique;
      owner is one of the four roles; Fix not empty; every label
      has a block with Risk, Owner, Fix, Verify (not empty) and
      Agent task (null, or text naming dry_run and approval)

Market facts come from references/markets.json (override with --markets-file).

Output: one line per finding, "FILE:LINE: Cnn [ERROR|WARN] message", then a
tally. --json prints a JSON list instead. Stdlib only, Python 3.8+.

Usage:
  python3 scripts/validate_crm_output.py DRAFT.md --mode flow --piece journey \
      --markets "DE,SE" --operator "Acme Bet" --forbid "Other Brand"
  python3 scripts/validate_crm_output.py - --mode blueprint < draft.md

Exit codes:
  0  no errors (warnings allowed unless --strict)
  1  at least one error
  2  could not run: usage error, unreadable file, bad flag combination,
     missing or malformed markets file
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REF_DATA_MODEL = SKILL_DIR / "references" / "data-model.md"
REF_EVENTS = SKILL_DIR / "references" / "event-taxonomy.md"
REF_MARKETS = SKILL_DIR / "references" / "markets.json"

ENUMS = {
    "self_exclusion_source": {"operator_internal", "national_register", "support_agent", "multi_operator_scheme"},
    "nl_affordability_check_status": {"not_required", "pending", "passed", "failed"},
    "kyc_status": {"not_started", "in_progress", "approved", "provisional_allowed", "rejected", "expired"},
    "account_status": {"active", "suspended", "restricted", "closed", "pending_verification"},
    "country_license_status": {"licensed", "unlicensed", "pending", "restricted"},
    "rg_risk_level": {"low", "medium", "high", "severe"},
    "aml_status": {"clear", "monitoring", "blocked", "frozen", "restricted"},
    "preferred_product": {"casino", "sportsbook", "poker", "mixed", "unknown"},
    "vip_tier": {"none", "bronze", "silver", "gold", "platinum", "diamond"},
    "vip_status": {"standard", "vip", "host_managed"},
}

DIMENSIONS = [
    "journey_id", "type", "trigger", "entry_conditions", "exit_conditions",
    "subscription_topic", "suppression_checks", "frequency_cap", "flow_steps",
    "wait_times", "branch_logic", "email_purpose", "personalisation_fields",
    "conversion_event", "guardrail_metrics", "compliance_notes",
]
DIM_ALIASES = {
    "flow_steps_summary": "flow_steps",
    "branch_logic_summary": "branch_logic",
    "personalization_fields": "personalisation_fields",
    "id": "journey_id",
    "topic": "subscription_topic",
    "entry": "entry_conditions",
    "exit": "exit_conditions",
}

SECTIONS = [
    "Executive CRM Architecture",
    "Customer/Profile Attribute Schema",
    "Event Taxonomy",
    "Master Segments",
    "Global Suppression Framework",
    "Subscription Center and Topics",
    "Journey Map",
    "Detailed Flow Logic",
    "Email Content Matrix",
    "Responsible Gambling Automation",
    "Frequency Caps",
    "Prioritisation and Conflict Rules",
    "Reporting Dashboard",
    "A/B Testing Framework",
    "Implementation Checklist",
    "QA and Launch Checklist",
    "Legal/Compliance Questions",
]

# The Customer.io Liquid tag list (references/liquid-patterns.md, Allowed tags).
LIQUID_TAGS = {
    "if", "elsif", "else", "endif", "unless", "endunless", "case", "when", "endcase",
    "for", "endfor", "break", "continue", "cycle",
    "capture", "endcapture", "comment", "endcomment", "raw", "endraw", "assign",
    # Customer.io tags (all single tags)
    "cio_link", "cio_link_id", "render_liquid", "view_in_browser_url",
    "manage_subscription_preferences_url", "tracking_consent_url", "unsubscribe",
    "unsubscribe_url", "subscription_topic_name", "countdown", "random", "generate_uuid",
}
LIQUID_PAIRS = {"if": "endif", "unless": "endunless", "case": "endcase", "for": "endfor",
                "capture": "endcapture", "comment": "endcomment", "raw": "endraw"}
LIQUID_CLOSERS = {v: k for k, v in LIQUID_PAIRS.items()}
LIQUID_CHILDREN = {"elsif": {"if", "unless"}, "else": {"if", "unless", "case", "for"},
                   "when": {"case"}, "break": {"for"}, "continue": {"for"}}

GATE_TERMS = [
    ("marketing_blocked", r"\bmarketing_blocked\b"),
    ("self_excluded", r"\bself_excluded\b"),
    ("timeout_active", r"\btimeout_active\b"),
    ("rg_risk_level", r"\brg_risk_level\b"),
    ("account_status", r"\baccount_status\b"),
    ("email_marketing_consent", r"\bemail_marketing_consent\b"),
    ("age_verified", r"\bage_verified\b"),
    ("kyc_status", r"\bkyc_status\b"),
    ("unsubscribed", r"\bunsubscribed\b"),
    ("country_license_status", r"\bcountry_license_status\b"),
    ("aml_status", r"\baml_status\b"),
    ("fraud_flag", r"\bfraud_flag\b"),
    ("topic", r"\btopic"),
    ("frequency cap", r"frequency[ _]cap|marketing_emails_sent_last_7d"),
]

RISK_ORDER = ["player-protection", "compliance", "revenue", "hygiene"]
JOURNEY_ID_RE = re.compile(r"^JRN_(TXN|SVC|MKT|VIP|RG|SYS)_\d{2}(_[A-Za-z0-9_]+)?$")
CATALOGUE_ID_RE = re.compile(r"^(JRN_)?(TXN|SVC|MKT|VIP|RG|SYS)_\d{2}(_[A-Za-z0-9_]+)?$")
TYPE_WORDS = {
    "TXN": ("transactional",), "SVC": ("service", "transactional"),
    "MKT": ("marketing", "promotional"), "VIP": ("vip", "marketing", "loyalty"),
    "RG": ("responsible", "rg", "protective"), "SYS": ("system", "transactional"),
}
OPERATOR_RE = re.compile(r"==|!=|>=|<=|<|>|\bNOT IN\b|\bIN\b|\bBETWEEN\b|\bis\b|\bone of\b")
ATTR_COND_RE = re.compile(
    r"\b(?<!event\.)(?:customer\.)?([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\s*(?:==|!=|>=|<=|<|>|\bNOT IN\b|\bIN\b|\bBETWEEN\b|\bis\b)")
ENUM_RE = re.compile(
    r"\b(" + "|".join(ENUMS) + r")\b\s*"
    r"(==|!=|\bNOT IN\b|\bIN\b|\bis not one of\b|\bis one of\b|\bis not\b|\bis\b|\bchanges to\b)\s*:?\s*"
    r"(\[[^\]]*\]|\([^)]*\)|\"[^\"]*\"|'[^']*'|[A-Za-z_]+(?:\s*,\s*[A-Za-z_]+)*)")
SNAKE_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
EMPTY_CELLS = {"", "-", "—", "–", "n/a", "na", "none"}
VERIFY_MARKER = "(verify before deployment)"

# Placeholder patterns for C02. Words are written with character classes so a
# plain-text search of the skill for placeholder words finds only fixtures.
PLACEHOLDER_RES = [
    (re.compile(r"\[(T[B]D|TO[D]O|in[s]ert[^\]]*|placeholder|XXX)\]", re.I), "bracketed placeholder"),
    (re.compile(r"\bTO[D]O\b"), "bare to-do marker"),
    (re.compile(r"\bT[B]D\b"), "bare to-be-decided marker"),
    (re.compile(r"\bFIX[M]E\b"), "fix-me marker"),
    (re.compile(r"\bin[s]ert\b.{0,40}\bhere\b", re.I), "'insert ... here' text"),
    (re.compile(r"lorem ipsum", re.I), "lorem ipsum"),
    (re.compile(r"\bas appropriate\b", re.I), "'as appropriate' instead of a concrete rule"),
    (re.compile(r"<your[^>]*>", re.I), "'<your ...>' slot"),
    (re.compile(r"\[F[I]LL", re.I), "fill marker"),
]
SLOT_RE = re.compile(r"\[([A-Z][A-Z0-9_]{2,})\]")


class Report:
    def __init__(self, path: str):
        self.path = path
        self.items = []

    def add(self, level: str, line: int, rule: str, msg: str) -> None:
        self.items.append({"file": self.path, "line": line, "level": level, "rule": rule, "message": msg})

    def error(self, line: int, rule: str, msg: str) -> None:
        self.add("ERROR", line, rule, msg)

    def warn(self, line: int, rule: str, msg: str) -> None:
        self.add("WARN", line, rule, msg)


def split_cells(line: str) -> list:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, in_code, i = [], [], False, 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if c == "`":
            in_code = not in_code
        if c == "|" and not in_code:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def norm(text: str) -> str:
    return text.strip().strip("`*").strip().lower()


def norm_key(text: str) -> str:
    k = re.sub(r"[\s\-]+", "_", norm(text))
    return DIM_ALIASES.get(k, k)


class Table:
    def __init__(self, line: int, header: list, rows: list):
        self.line = line          # 1-based line of the header
        self.header = header      # normalised header cells
        self.rows = rows          # list of (line, cells)

    def col(self, *words: str) -> int:
        for i, h in enumerate(self.header):
            if any(w in h for w in words):
                return i
        return -1


class Doc:
    def __init__(self, text: str):
        self.text = text
        self.lines = text.splitlines()
        self.in_fence = [False] * len(self.lines)
        self.fences = []          # dicts: lang, start, end (0-based, end None if unclosed)
        self.fence_markers = 0
        self._parse_fences()
        self.headings = []        # (line0, level, title)
        self.tables = []
        self._parse_prose()

    def _parse_fences(self) -> None:
        open_f = None
        for i, ln in enumerate(self.lines):
            m = re.match(r"^\s{0,3}(`{3,}|~{3,})\s*([\w+-]*)", ln)
            if m:
                self.fence_markers += 1
                self.in_fence[i] = True
                if open_f is None:
                    open_f = {"lang": m.group(2).lower(), "start": i, "end": None, "char": m.group(1)[0]}
                elif m.group(1)[0] == open_f["char"] and not m.group(2):
                    open_f["end"] = i
                    self.fences.append(open_f)
                    open_f = None
                continue
            if open_f is not None:
                self.in_fence[i] = True
        if open_f is not None:
            self.fences.append(open_f)

    def _parse_prose(self) -> None:
        i, n = 0, len(self.lines)
        while i < n:
            ln = self.lines[i]
            if self.in_fence[i]:
                i += 1
                continue
            m = re.match(r"^(#{1,6})\s+(.*)$", ln)
            if m:
                self.headings.append((i, len(m.group(1)), m.group(2).strip()))
                i += 1
                continue
            if ln.strip().startswith("|") and i + 1 < n and not self.in_fence[i + 1] \
                    and re.match(r"^\s*\|?\s*:?-{2,}", self.lines[i + 1]):
                header = [norm(c) for c in split_cells(ln)]
                rows, j = [], i + 2
                while j < n and not self.in_fence[j] and self.lines[j].strip().startswith("|"):
                    rows.append((j + 1, split_cells(self.lines[j])))
                    j += 1
                self.tables.append(Table(i + 1, header, rows))
                i = j
                continue
            i += 1

    def fence_text(self, fence: dict) -> tuple:
        end = fence["end"] if fence["end"] is not None else len(self.lines)
        return fence["start"] + 2, "\n".join(self.lines[fence["start"] + 1:end])

    def prose_paragraphs(self) -> list:
        paras, cur, start = [], [], None
        for i, ln in enumerate(self.lines):
            if self.in_fence[i] or not ln.strip():
                if cur:
                    paras.append((start + 1, "\n".join(cur)))
                cur, start = [], None
                continue
            if start is None:
                start = i
            cur.append(ln)
        if cur:
            paras.append((start + 1, "\n".join(cur)))
        return paras


def ref_tokens(path: Path) -> set:
    """Backticked identifiers in the first cell of every table row of a reference."""
    found = set()
    if not path.is_file():
        return found
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ln.strip().startswith("|"):
            first = split_cells(ln)[0]
            for tok in re.findall(r"`([a-z][a-z0-9_]*)`", first):
                found.add(tok)
    return found


def line_of(doc: Doc, pos: int) -> int:
    return doc.text.count("\n", 0, pos) + 1


# ---------------------------------------------------------------- journeys

def collect_journeys(doc: Doc, rep: Report) -> dict:
    events = []
    for (i, _lvl, title) in doc.headings:
        m = re.search(r"\bJRN_[A-Za-z0-9_]+", title)
        if m:
            events.append((i + 1, "heading", m.group(0), None))
    for t in doc.tables:
        if t.header[:2] == ["dimension", "specification"]:
            dims = {}
            for (ln, cells) in t.rows:
                if len(cells) >= 2:
                    dims[norm_key(cells[0])] = (cells[1].strip(), ln)
            jid = dims.get("journey_id", ("", t.line))[0].strip("`* ")
            events.append((t.line, "spec", jid or None, dims))
        elif t.col("step") >= 0 and t.col("action") >= 0:
            events.append((t.line, "flow", None, t))
    events.sort(key=lambda e: e[0])
    journeys, current = {}, None
    for (line, kind, jid, payload) in events:
        if kind in ("heading", "spec") and jid:
            current = jid
            journeys.setdefault(jid, {"spec": None, "flows": [], "line": line})
        if kind == "spec":
            key = jid or "(spec without journey_id at line %d)" % line
            journeys.setdefault(key, {"spec": None, "flows": [], "line": line})
            journeys[key]["spec"] = payload
            journeys[key]["spec_line"] = line
        elif kind == "flow":
            key = current or "(flow table at line %d)" % line
            journeys.setdefault(key, {"spec": None, "flows": [], "line": line})
            journeys[key]["flows"].append(payload)
    return journeys


def jtype(jid: str) -> str:
    m = re.match(r"^JRN_(TXN|SVC|MKT|VIP|RG|SYS)_", jid or "")
    return m.group(1) if m else ""


def dim(spec: dict, key: str) -> tuple:
    return spec.get(key, ("", 0))


OFFER_RE = re.compile(r"\b(bonus(es)?|free spins?|reload|free bets?|offers?|cashback)\b", re.I)
NO_OFFER_RE = re.compile(r"\b(no|without|not an?)\s+(offers?|bonus(es)?)\b", re.I)


def is_offer(text: str) -> bool:
    """True when the text describes an offer; negations such as 'no offer' are ignored."""
    return bool(OFFER_RE.search(NO_OFFER_RE.sub(" ", text or "")))


def journey_text(j: dict) -> str:
    parts = []
    if j["spec"]:
        parts.extend(v for (v, _l) in j["spec"].values())
    for t in j["flows"]:
        for (_ln, cells) in t.rows:
            parts.extend(cells)
    return "\n".join(parts)


def check_journeys(doc: Doc, rep: Report, mode: str, piece: str, known_events: set = frozenset()) -> dict:
    journeys = collect_journeys(doc, rep)
    active = mode == "blueprint" or (mode == "flow" and piece == "journey")
    if not active:
        return journeys
    if mode == "flow" and not any(j["spec"] for j in journeys.values()):
        rep.error(1, "C03", "FLOW journey deliverable has no journey spec table (header 'Dimension | Specification')")
    for jid, j in journeys.items():
        spec = j["spec"]
        t = jtype(jid)
        if spec is None:
            if j["flows"]:
                rep.error(j["line"], "C03", "journey %s has a flow table but no 16-dimension spec table" % jid)
        else:
            sl = j.get("spec_line", j["line"])
            for d in DIMENSIONS:
                val, ln = dim(spec, d)
                if norm(val) in EMPTY_CELLS:
                    rep.error(ln or sl, "C03", "journey %s: dimension '%s' missing, empty or '%s'" % (jid, d, val))
            if not JOURNEY_ID_RE.match(jid):
                rep.error(sl, "C04", "journey ID '%s' does not match JRN_<TXN|SVC|MKT|VIP|RG|SYS>_NN_Name" % jid)
            elif t:
                tv, tl = dim(spec, "type")
                if tv and not any(w in tv.lower() for w in TYPE_WORDS[t]):
                    rep.error(tl, "C04", "journey %s: type '%s' does not match prefix %s" % (jid, tv, t))
            trig, trl = dim(spec, "trigger")
            evs = [e for e in dict.fromkeys(re.findall(r"`([a-z][a-z0-9_]*)`", trig)) if e in known_events]
            if len(evs) >= 2 and not re.search(r"normali[sz]ed|attribute trigger|segment trigger", trig, re.I):
                rep.warn(trl or sl, "C25", "journey %s: trigger names %d events (%s); an event trigger takes one "
                         "event: use a normalised event or an attribute/segment trigger" % (jid, len(evs), ", ".join(evs)))
            topic, topl = dim(spec, "subscription_topic")
            cap, capl = dim(spec, "frequency_cap")
            if t in ("MKT", "VIP"):
                entry, el = dim(spec, "entry_conditions")
                exitc, xl = dim(spec, "exit_conditions")
                if "SEG_CAN_RECEIVE_MARKETING" not in entry:
                    rep.error(el or sl, "C06", "marketing journey %s: entry does not include SEG_CAN_RECEIVE_MARKETING" % jid)
                full_set = all(re.search(p, exitc, re.I) for p in (
                    r"self_excluded|SEG_SELF_EXCLUDED", r"timeout|SEG_TIMEOUT_ACTIVE", r"high",
                    r"unsubscribed|SEG_UNSUBSCRIBED", r"aml|SEG_AML_RESTRICTED"))
                if "SEG_RG_SUPPRESSED" not in exitc and not full_set:
                    rep.error(xl or sl, "C06", "marketing journey %s: exit does not include SEG_RG_SUPPRESSED (or the full gate exit set)" % jid)
                core = ("marketing_blocked", "self_excluded", "timeout_active", "rg_risk_level")
                if "RG_EXIT_BLOCK" not in exitc and not all(re.search(r"\b%s\b" % c, exitc) for c in core):
                    rep.error(xl or sl, "C22", "marketing journey %s: exit does not include RG_EXIT_BLOCK "
                              "(templates/rg-exit-block.md)" % jid)
                if re.search(r"transactional|safer gambling", topic, re.I):
                    rep.error(topl or sl, "C06", "marketing journey %s: topic '%s' is not a marketing topic" % (jid, topic))
                if "exempt" in cap.lower() or not re.search(r"\d", cap):
                    rep.error(capl or sl, "C06", "marketing journey %s: frequency cap must be numeric, not '%s'" % (jid, cap))
            elif t in ("RG", "TXN", "SVC", "SYS"):
                if not re.search(r"transactional|safer gambling|account|service", topic, re.I) or \
                        re.search(r"offers|loyalty|promotion", topic, re.I):
                    rep.error(topl or sl, "C08", "journey %s: topic '%s' must be non-marketing (Transactional or Safer Gambling)" % (jid, topic))
                if "exempt" not in cap.lower():
                    rep.error(capl or sl, "C08", "journey %s: frequency cap must be Exempt, not '%s'" % (jid, cap))
        # C07 per flow table
        for tbl in j["flows"]:
            gi, ai = tbl.col("gate"), tbl.col("action")
            if gi < 0:
                rep.error(tbl.line, "C07", "flow table for %s has no Gate column" % jid)
                continue
            if t not in ("MKT", "VIP"):
                continue
            for idx, (ln, cells) in enumerate(tbl.rows):
                action = cells[ai].lower() if ai < len(cells) else ""
                if not action.startswith("email"):
                    continue
                gate = norm(cells[gi]) if gi < len(cells) else ""
                if gate in EMPTY_CELLS:
                    prev = [norm(r[1][ai]) if ai < len(r[1]) else "" for r in tbl.rows[max(0, idx - 2):idx]]
                    if not (len(prev) == 2 and prev[0].startswith("webhook") and prev[1].startswith("branch")):
                        rep.error(ln, "C07", "marketing journey %s: Email row has no gate (needs MKT/BONUS or a preceding Webhook verify + Branch)" % jid)
                elif gate == "txn":
                    rep.error(ln, "C07", "marketing journey %s: Email row uses the transactional gate" % jid)
        # C09 bonus content: every offer Email row carries the BONUS gate code
        if t in ("MKT", "VIP"):
            focus = []
            if spec:
                for k in ("email_purpose", "flow_steps", "branch_logic"):
                    focus.append(dim(spec, k)[0])
            for tbl in j["flows"]:
                gi, ai = tbl.col("gate"), tbl.col("action")
                pc, sc = tbl.col("purpose"), tbl.col("subject")
                for (ln, cells) in tbl.rows:
                    texts = [cells[c] for c in (pc, sc) if 0 <= c < len(cells)]
                    focus.extend(texts)
                    action = cells[ai].lower() if 0 <= ai < len(cells) else ""
                    if not action.startswith("email") or gi < 0:
                        continue
                    if is_offer(" ".join(texts)) and (norm(cells[gi]) if gi < len(cells) else "") != "bonus":
                        rep.error(ln, "C09", "journey %s: offer Email row must carry Gate BONUS (found '%s')"
                                  % (jid, cells[gi] if gi < len(cells) else ""))
            if is_offer(" ".join(focus)):
                alltext = journey_text(j)
                gates = [norm(cells[tbl.col("gate")]) for tbl in j["flows"] if tbl.col("gate") >= 0
                         for (_ln, cells) in tbl.rows if tbl.col("gate") < len(cells)]
                if "SEG_CAN_RECEIVE_BONUS" not in alltext and "bonus_abuse_flag" not in alltext and "bonus" not in gates:
                    rep.error(j.get("spec_line", j["line"]), "C09",
                              "journey %s offers a bonus but never references SEG_CAN_RECEIVE_BONUS or bonus_abuse_flag" % jid)
    return journeys


def check_journey_ids(doc: Doc, rep: Report) -> None:
    catalogue_cells = set()
    for t in doc.tables:
        if t.col("id") == 0 and t.col("trigger") >= 0 and t.col("entry") >= 0:
            for (ln, cells) in t.rows:
                v = cells[0].strip("`* ")
                catalogue_cells.add(ln)
                if not CATALOGUE_ID_RE.match(v):
                    rep.error(ln, "C04", "catalogue journey ID '%s' is not TYPE_NN or JRN_TYPE_NN_Name" % v)
    for m in re.finditer(r"\bJRN_[A-Za-z0-9_]*", doc.text):
        tok = m.group(0).rstrip("_")
        if tok == "JRN":
            continue
        if not JOURNEY_ID_RE.match(tok) and not re.match(r"^JRN_(TXN|SVC|MKT|VIP|RG|SYS)$", tok):
            rep.error(line_of(doc, m.start()), "C04", "journey ID '%s' does not match JRN_<TYPE>_NN_Name" % tok)


# ---------------------------------------------------------------- segments

def segment_defs(doc: Doc) -> list:
    """(line, segment, logic) for segment table rows, Logic: lines and := lines."""
    defs = []
    for t in doc.tables:
        si, li = t.col("segment"), t.col("logic", "condition")
        if si >= 0 and li >= 0 and si != li:
            for (ln, cells) in t.rows:
                if max(si, li) < len(cells):
                    defs.append((ln, cells[si], cells[li]))
    for i, ln in enumerate(doc.lines):
        m = re.match(r"^\s*(?:[-*]\s*)?\*\*Logic:?\*\*:?\s*(.+)$|^Logic:\s*(.+)$", ln)
        if m and not doc.in_fence[i]:
            defs.append((i + 1, "", m.group(1) or m.group(2)))
        m = re.match(r"^\s*(SEG_[A-Za-z0-9_]+)\s*:=\s*(.*)$", ln)
        if m:
            defs.append((i + 1, m.group(1), m.group(2)))
    return defs


def check_segments(doc: Doc, rep: Report, mode: str, piece: str) -> list:
    defs = segment_defs(doc)
    if not (mode == "blueprint" or (mode == "flow" and piece in ("segments", "journey"))):
        return defs
    for m in re.finditer(r"\bSEG_[A-Za-z0-9_]*", doc.text):
        tok = m.group(0)
        if tok == "SEG_":
            continue
        if not re.match(r"^SEG_[A-Z0-9_]+$", tok):
            rep.error(line_of(doc, m.start()), "C05", "segment ID '%s' is not SEG_UPPER_SNAKE" % tok)
    for (ln, seg, logic) in defs:
        if logic.strip() and not OPERATOR_RE.search(logic):
            rep.error(ln, "C05", "segment %s logic has no operator (prose instead of a condition): '%s'" % (seg or "", logic[:60]))
    if mode == "flow" and piece == "segments" and not defs:
        rep.error(1, "C05", "FLOW segments deliverable defines no segment logic (table with Segment and Logic columns)")
    return defs


# ---------------------------------------------------------------- liquid

def check_liquid_block(text: str, start_line: int, rep: Report, strict=None) -> None:
    def ln_at(pos: int) -> int:
        return start_line + text.count("\n", 0, pos)

    assigned = set(re.findall(r"\{%-?\s*(?:assign|capture|for)\s+(\w+)", text))
    for m in re.finditer(r"\{\{-?(.{0,300}?)-?\}\}", text):
        expr = m.group(1).strip()
        head = re.split(r"[\s|]", expr, maxsplit=1)[0] if expr else ""
        if "default" in expr or not head or head[0] in "\"'0123456789" \
                or head.split(".")[0] in assigned or head == "customer.id":
            continue
        line = ln_at(m.start())
        owner = strict(line) if strict else None
        if owner:
            rep.error(line, "C29", "Liquid output '{{ %s }}' in %s has no | default: fallback; transactional "
                      "messages send even when Liquid fails" % (expr[:40], owner))
        else:
            rep.warn(line, "C10", "Liquid output '{{ %s }}' has no | default: fallback" % expr[:40])
    stripped = re.sub(r"\{\{.{0,300}?\}\}", lambda m: " " * len(m.group(0)), text)
    for m in re.finditer(r"\{\{", stripped):
        rep.error(ln_at(m.start()), "C10", "unclosed Liquid output '{{' (no matching '}}')")
    tags = list(re.finditer(r"\{%-?\s*(\w*)(.{0,300}?)-?%\}", text, re.S))
    rest = re.sub(r"\{%.{0,300}?%\}", lambda m: " " * len(m.group(0)), text, flags=re.S)
    for m in re.finditer(r"\{%", rest):
        rep.error(ln_at(m.start()), "C10", "unclosed Liquid tag '{%' (no matching '%}')")
    for m in re.finditer(r"%\}", rest):
        rep.error(ln_at(m.start()), "C10", "stray '%}' with no opening '{%'")
    stack, verbatim = [], None
    for m in tags:
        name = m.group(1).lower()
        line = ln_at(m.start())
        if verbatim:
            if name == "end" + verbatim:
                stack.pop()
                verbatim = None
            continue
        if not name:
            rep.error(line, "C10", "Liquid tag with no name")
            continue
        if name not in LIQUID_TAGS:
            rep.error(line, "C10", "non-standard Liquid tag '%s' (not in the Customer.io tag list)" % name)
            continue
        if name == "countdown":
            rep.warn(line, "C10", "countdown tag: check the false-urgency rubric (references/kpis-and-testing.md)")
        if name in LIQUID_PAIRS:
            stack.append((name, line))
            if name in ("raw", "comment"):
                verbatim = name
        elif name in LIQUID_CLOSERS:
            opener = LIQUID_CLOSERS[name]
            if not stack:
                rep.error(line, "C10", "'%s' without an open '%s'" % (name, opener))
            elif stack[-1][0] != opener:
                rep.error(line, "C10", "'%s' closes '%s' opened at line %d (bad nesting)" % (name, stack[-1][0], stack[-1][1]))
                stack.pop()
            else:
                stack.pop()
        elif name in LIQUID_CHILDREN:
            if not any(s[0] in LIQUID_CHILDREN[name] for s in stack):
                rep.error(line, "C10", "'%s' outside a %s block" % (name, "/".join(sorted(LIQUID_CHILDREN[name]))))
    for (name, line) in stack:
        rep.error(line, "C10", "'%s' is never closed with '%s'" % (name, LIQUID_PAIRS[name]))


def protected_spans(doc: Doc) -> list:
    """(start, end, journey_id) line spans of TXN/SVC/SYS/RG journey sections, by JRN_ headings."""
    heads = []
    for (i, _lvl, title) in doc.headings:
        m = re.search(r"\bJRN_[A-Za-z0-9_]+", title)
        if m:
            heads.append((i + 1, m.group(0)))
    spans = []
    for k, (line, jid) in enumerate(heads):
        end = heads[k + 1][0] - 1 if k + 1 < len(heads) else len(doc.lines)
        if jtype(jid) in ("TXN", "SVC", "SYS", "RG"):
            spans.append((line, end, jid))
    return spans


def check_liquid(doc: Doc, rep: Report) -> None:
    spans = protected_spans(doc)

    def strict(line: int):
        for (a, b, jid) in spans:
            if a <= line <= b:
                return jid
        return None
    for f in doc.fences:
        start, text = doc.fence_text(f)
        check_liquid_block(text, start, rep, strict)
    for (start, text) in doc.prose_paragraphs():
        check_liquid_block(text, start, rep, strict)


# ---------------------------------------------------------------- waits and conditions

WAIT_MAX_RE = re.compile(r"\bmax(?:imum)?\.?(?:\s+time)?\s*[:=]?\s*\d+\s*(?:h|hrs?|hours?|d|days?|min|minutes?|w|weeks?)\b",
                         re.I)


def check_waits(doc: Doc, rep: Report, journeys: dict) -> None:
    for t in doc.tables:
        ai, wi = t.col("action"), t.col("wait")
        if t.col("step") < 0 or ai < 0:
            continue
        for (ln, cells) in t.rows:
            if ai >= len(cells) or not norm(cells[ai]).startswith("wait"):
                continue
            # the until clause may sit in the Wait column or in the Action cell ("Wait Until ...")
            w = " ".join(c for c in (cells[ai], cells[wi] if 0 <= wi < len(cells) else "") if c)
            if re.search(r"\buntil\b", w, re.I) and not WAIT_MAX_RE.search(w):
                rep.error(ln, "C23", "Wait Until '%s' has no fixed Max time (write 'max 35 d'); without one a "
                          "player can wait forever" % w[:50])
    for jid, j in journeys.items():
        if not j["spec"]:
            continue
        val, ln = dim(j["spec"], "wait_times")
        if len(re.findall(r"\buntil\b", val, re.I)) > len(WAIT_MAX_RE.findall(val)):
            rep.error(ln, "C23", "journey %s: a wait-until in wait_times has no fixed Max time" % jid)


ATTR_TOKEN = r"(?:customer\.|event\.)?[a-z][a-z0-9]*(?:_[a-z0-9]+)+"
ATTR_VS_ATTR_RE = re.compile(r"(?<![\w.\"'])(" + ATTR_TOKEN + r")\s*(==|!=|>=|<=|<|>)\s*(" + ATTR_TOKEN + r")(?![\w\"'(])")
ENUM_VALUES = set().union(*ENUMS.values())


def check_attr_compare(doc: Doc, rep: Report, journeys: dict, segdefs: list) -> None:
    cands = [(ln, logic) for (ln, _s, logic) in segdefs]
    for j in journeys.values():
        if j["spec"]:
            for k in ("entry_conditions", "exit_conditions", "branch_logic"):
                val, ln = dim(j["spec"], k)
                cands.append((ln, val))
        for t in j["flows"]:
            bi = t.col("branch")
            for (ln, cells) in t.rows:
                if 0 <= bi < len(cells):
                    cands.append((ln, cells[bi]))
    seen = set()
    for (ln, text) in cands:
        for m in ATTR_VS_ATTR_RE.finditer(text or ""):
            lhs, rhs = m.group(1), m.group(3)
            if rhs.split(".")[-1] in ENUM_VALUES or (ln, m.group(0)) in seen:
                continue
            seen.add((ln, m.group(0)))
            l, r = lhs.split(".")[-1], rhs.split(".")[-1]
            rep.error(ln, "C24", "'%s' compares two attributes; segments and filters cannot: compute "
                      "`%s_gt_%s` (or a flag) in the backend" % (m.group(0), l, r))


# ---------------------------------------------------------------- fences

def check_fences(doc: Doc, rep: Report) -> None:
    for f in doc.fences:
        if f["end"] is None:
            rep.error(f["start"] + 1, "C11", "code fence opened here is never closed")
    if doc.fence_markers % 2:
        rep.error(len(doc.lines), "C11", "odd number of code fence markers (%d)" % doc.fence_markers)
    for f in doc.fences:
        if f["lang"] != "json" or f["end"] is None:
            continue
        start, text = doc.fence_text(f)
        if "{{" in text or "{%" in text:
            continue
        body = "\n".join(l for l in text.splitlines() if not l.strip().startswith("//"))
        try:
            json.loads(body)
        except ValueError as exc:
            rep.error(start, "C11", "json fence does not parse: %s" % exc)


# ---------------------------------------------------------------- blueprint

def title_key(title: str) -> str:
    t = title.lower().replace("&", " and ")
    t = t.replace("centre", "center").replace("prioritization", "prioritisation")
    return re.sub(r"[^a-z0-9]", "", t)


SECTION_KEYS = [title_key(s) for s in SECTIONS]


def check_sections(doc: Doc, rep: Report) -> dict:
    found = []  # (line, number_or_None, index)
    spans = {}
    for (i, lvl, title) in doc.headings:
        m = re.match(r"^(?:section\s+)?(\d{1,2})\s*[.:)]?\s*[—–:-]?\s*(.*)$", title, re.I)
        num, rest = (int(m.group(1)), m.group(2)) if m else (None, title)
        key = title_key(rest)
        if key in SECTION_KEYS:
            found.append((i + 1, num, SECTION_KEYS.index(key), lvl))
        elif num is not None and re.match(r"^section\s", title, re.I):
            rep.error(i + 1, "C12", "section heading '%s' does not match a canonical title" % title)
    seen = {}
    for (line, num, idx, _lvl) in found:
        if idx in seen:
            rep.error(line, "C12", "duplicate section '%s' (first at line %d)" % (SECTIONS[idx], seen[idx]))
            continue
        seen[idx] = line
        if num is not None and num != idx + 1:
            rep.error(line, "C12", "section '%s' is numbered %d, expected %d" % (SECTIONS[idx], num, idx + 1))
    for idx, s in enumerate(SECTIONS):
        if idx not in seen:
            rep.error(1, "C12", "missing section %d. %s" % (idx + 1, s))
    order = [idx for (_l, _n, idx, _v) in sorted(found)]
    firsts = []
    for idx in order:
        if idx not in firsts:
            firsts.append(idx)
    if firsts != sorted(firsts):
        rep.error(1, "C12", "sections are out of canonical order: %s" % ", ".join(str(i + 1) for i in firsts))
    # spans for C20
    heads = sorted((line, idx) for (line, _n, idx, _v) in found)
    for k, (line, idx) in enumerate(heads):
        end = heads[k + 1][0] - 1 if k + 1 < len(heads) else len(doc.lines)
        spans.setdefault(idx, (line, end))
    return spans


def as_int(cell: str):
    c = norm(cell)
    if re.match(r"^\d+$", c):
        return int(c)
    return None


def check_caps(doc: Doc, rep: Report, required: bool) -> None:
    tables = [t for t in doc.tables
              if t.col("daily") >= 0 and t.col("weekly") >= 0 and t.col("daily") != t.col("weekly")]
    if not tables:
        if required:
            rep.error(1, "C13", "no frequency cap table (columns segment, daily, weekly, cooldown, bonus, cross-sell)")
        return
    seen_keys = ""
    for t in tables:
        di, wi, ci = t.col("daily"), t.col("weekly"), t.col("cool")
        bi, xi = t.col("bonus"), t.col("cross")
        for name, idx in (("cooldown", ci), ("bonus", bi), ("cross-sell", xi)):
            if idx < 0:
                rep.error(t.line, "C13", "cap table has no %s column" % name)
        for (ln, cells) in t.rows:
            seg = norm(cells[0]) if cells else ""
            seen_keys += " " + seg
            vals = {}
            for name, idx in (("daily", di), ("weekly", wi), ("bonus", bi), ("cross-sell", xi)):
                if idx < 0 or idx >= len(cells):
                    continue
                c = norm(cells[idx])
                if c == "n/a":
                    vals[name] = None
                elif re.match(r"^\d+$", c):
                    vals[name] = int(c)
                else:
                    rep.error(ln, "C13", "cap table '%s' %s value '%s' is not an integer or n/a" % (seg, name, cells[idx]))
            if 0 <= ci < len(cells):
                c = norm(cells[ci])
                if c != "n/a" and not re.match(r"^\d+\s*[hd]?$", c):
                    rep.error(ln, "C13", "cap table '%s' cooldown '%s' is not hours, days or n/a" % (seg, cells[ci]))
            d, w = vals.get("daily"), vals.get("weekly")
            if d is not None and w is not None and d > w:
                rep.error(ln, "C13", "cap table '%s': daily %d exceeds weekly %d" % (seg, d, w))
            if re.search(r"rg_high|rg_severe|timeout|self_excluded", seg):
                for name in ("daily", "weekly", "bonus", "cross-sell"):
                    if name in vals and vals[name] != 0:
                        rep.error(ln, "C13", "cap table '%s': %s must be 0 for RG high/severe, timeout, self-excluded" % (seg, name))
            if "rg_medium" in seg:
                for name in ("bonus", "cross-sell"):
                    if name in vals and vals[name] != 0:
                        rep.error(ln, "C13", "cap table rg_medium: %s must be 0" % name)
    if required:
        for key in ("rg_medium", "rg_high", "rg_severe", "timeout", "self_excluded"):
            if key not in seen_keys:
                rep.error(tables[0].line, "C13", "cap table has no row for %s" % key)


def check_priority(doc: Doc, rep: Report) -> None:
    tables = [t for t in doc.tables if t.col("level") >= 0 and t.col("journey") >= 0]
    if not tables:
        rep.error(1, "C14", "no priority table (columns Level and Journeys)")
        return
    t = tables[0]
    li = t.col("level")
    levels = {}
    for (ln, cells) in t.rows:
        m = re.search(r"\d+", cells[li]) if li < len(cells) else None
        if not m:
            rep.error(ln, "C14", "priority row has no numeric level")
            continue
        lv = int(m.group(0))
        if lv in levels:
            rep.error(ln, "C14", "priority level %d appears twice" % lv)
        levels[lv] = (ln, " ".join(cells))
    if sorted(levels) != list(range(1, 12)):
        rep.error(t.line, "C14", "priority levels must be exactly 1-11, found %s" % sorted(levels))
    if 1 in levels and "RG_12" not in levels[1][1]:
        rep.error(levels[1][0], "C14", "level 1 must contain RG_12")


# ---------------------------------------------------------------- other rules

NOTICE = ("Legal/compliance review required: have qualified legal and compliance counsel "
          "review this design in every target jurisdiction before deployment.")


def notice_key(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_>`]", "", text)).strip().lower()


def check_notice(doc: Doc, rep: Report) -> None:
    tail = [(i, l) for i, l in enumerate(doc.lines) if l.strip()][-3:]
    if not any(notice_key(l) == notice_key(NOTICE) for (_i, l) in tail):
        rep.error(len(doc.lines) or 1, "C15", "the canonical legal/compliance notice is not one of the last 3 "
                  "non-empty lines (text in protocols/self-check.md step 6)")


MARKET_KEYS = ("name", "market_status", "register", "api_check", "consent", "bonus_rules", "time_windows",
               "helpline", "source_url", "verified_on", "status", "notes")
BONUS_KEYS = ("max_wagering_multiplier", "single_product", "first_play_only", "deposit_conditional_allowed")
MARKET_ALIASES = {"GB": "UK", "GREAT_BRITAIN": "UK", "BRITAIN": "UK", "CANADA_ONTARIO": "ON"}


class MarketsError(Exception):
    pass


def load_markets(path: Path) -> dict:
    """Read and shape-check markets.json; raise MarketsError on any defect (exit 2)."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise MarketsError("cannot read markets file %s: %s" % (path, exc))
    except ValueError as exc:
        raise MarketsError("markets file %s is not valid JSON: %s" % (path, exc))
    if not isinstance(data, dict) or not isinstance(data.get("markets"), dict):
        raise MarketsError("markets file %s has no 'markets' object" % path)
    if not isinstance(data.get("stale_after_days", 180), int):
        raise MarketsError("markets file %s: stale_after_days must be an integer" % path)
    for code, row in data["markets"].items():
        if not isinstance(row, dict):
            raise MarketsError("market %s: row is not an object" % code)
        missing = [k for k in MARKET_KEYS if k not in row]
        if missing:
            raise MarketsError("market %s: missing key(s) %s" % (code, ", ".join(missing)))
        if row["status"] not in ("primary", "secondary", "unverified"):
            raise MarketsError("market %s: status '%s' is not primary|secondary|unverified" % (code, row["status"]))
        if row["market_status"] not in ("open", "closed_pending"):
            raise MarketsError("market %s: market_status '%s' is not open|closed_pending" % (code, row["market_status"]))
        if row["market_status"] == "closed_pending" and not row.get("status_note"):
            raise MarketsError("market %s: closed_pending needs a status_note" % code)
        if not isinstance(row["bonus_rules"], dict) or any(k not in row["bonus_rules"] for k in BONUS_KEYS):
            raise MarketsError("market %s: bonus_rules needs %s" % (code, ", ".join(BONUS_KEYS)))
        vo = row["verified_on"]
        if vo is not None:
            try:
                datetime.date.fromisoformat(vo)
            except (TypeError, ValueError):
                raise MarketsError("market %s: verified_on '%s' is not YYYY-MM-DD or null" % (code, vo))
        # full names ("Brazil", "United Kingdom", "Ontario (Canada)" and "Ontario") resolve to the code
        name = str(row.get("name") or "")
        for n in (name, re.sub(r"\s*\(.*?\)\s*", "", name)):
            if n.strip():
                MARKET_ALIASES.setdefault(alias_key(n), code)
    return data


def alias_key(text: str) -> str:
    return re.sub(r"[\s\-]+", "_", text.strip()).upper()


def market_code(mk: str) -> str:
    code = alias_key(mk)
    return MARKET_ALIASES.get(code, code)


def overlay_blocks(doc: Doc, mk: str) -> tuple:
    """(named, [(start_line0, end_line0, text)]) for headings or table rows naming the market."""
    code = market_code(mk)
    names = {mk.strip(), code} | {a.replace("_", " ") for a, c in MARKET_ALIASES.items() if c == code}

    def alt(n: str) -> str:
        # short codes match case-sensitively (so "ON" is not the word "on"); names ignore case
        body = r"\b%s\b" % re.escape(n)
        return body if len(n) <= 3 else "(?i:%s)" % body
    pat = re.compile("|".join(alt(n) for n in sorted(names, key=len, reverse=True)))
    named, blocks = False, []
    for (i, lvl, title) in doc.headings:
        if pat.search(title):
            named = True
            nxt = [h for h in doc.headings if h[0] > i and h[1] <= lvl]
            end = nxt[0][0] if nxt else len(doc.lines)
            blocks.append((i, end, "\n".join(doc.lines[i:end])))
    for t in doc.tables:
        for (ln, cells) in t.rows:
            if cells and pat.search(cells[0]):
                named = True
                blocks.append((ln - 1, ln, " ".join(cells)))
    return named, blocks


def check_markets(doc: Doc, rep: Report, markets: list, mdata: dict) -> None:
    rows = (mdata or {}).get("markets", {})
    for mk in markets:
        named, blocks = overlay_blocks(doc, mk)
        covering = [b for b in blocks if block_covers(b[2])]
        row = rows.get(market_code(mk))
        if not row and mdata:
            rep.warn(1, "C16", "no market row for '%s' in markets.json; C26/C27/C28 not evaluated: state "
                     "assumptions and add the LQ_* questions" % mk)
        if not covering:
            rep.error(1, "C16", "market '%s': no overlay block%s covering disclosures/helpline, register/suppression and RG"
                      % (mk, "" if named else " (market not named in any heading or table row)"))
            continue
        if not row:
            continue
        unverified = set(row.get("unverified_fields") or [])
        if row["status"] != "primary" or unverified:
            if not any(VERIFY_MARKER in b[2] for b in covering):
                rep.error(covering[0][0] + 1, "C16", "market '%s': markets.json row is %s; the overlay block must carry "
                          "'%s'" % (mk, row["status"] if row["status"] != "primary" else "partly unverified", VERIFY_MARKER))
            if row["status"] != "primary" or "helpline" in unverified:
                for (a, b, _t) in covering:
                    for i in range(a, b):
                        if re.search(r"helpline", doc.lines[i], re.I) and VERIFY_MARKER not in doc.lines[i]:
                            rep.error(i + 1, "C16", "market '%s': helpline line lacks '%s' (helpline not primary-verified)"
                                      % (mk, VERIFY_MARKER))


def check_market_freshness(rep: Report, markets: list, mdata: dict, today: datetime.date) -> None:
    rows, limit = mdata.get("markets", {}), mdata.get("stale_after_days", 180)
    for mk in markets:
        row = rows.get(market_code(mk))
        if not row or row["status"] == "unverified":
            continue
        vo = row["verified_on"]
        age = (today - datetime.date.fromisoformat(vo)).days if vo else None
        if age is None or age > limit:
            rep.warn(1, "C27", "market '%s': markets.json row (%s) verified_on %s is %s; re-verify before relying on it"
                     % (mk, row["status"], vo, "missing" if age is None else "%d days old (limit %d)" % (age, limit)))


def check_market_status(doc: Doc, rep: Report, markets: list, mdata: dict) -> None:
    rows = mdata.get("markets", {})
    top = [(i, l) for i, l in enumerate(doc.lines) if l.strip()][:20]
    for mk in markets:
        code = market_code(mk)
        row = rows.get(code)
        if not row or row["market_status"] != "closed_pending":
            continue
        ok = any(re.search(r"market status", l, re.I) and re.search(r"closed pending", l, re.I)
                 and re.search(r"\b%s\b" % re.escape(code), l) for (_i, l) in top)
        if ok:
            rep.warn(1, "C28", "market '%s' is %s: flows may be produced, but counsel must confirm legal status before "
                     "any send" % (mk, row["status_note"]))
        else:
            rep.error(1, "C28", "market '%s' is closed_pending: put the MARKET STATUS banner from markets.json in the first "
                      "20 lines: \"%s\"" % (mk, row.get("banner", "MARKET STATUS: %s %s" % (code, row["status_note"]))))


PRODUCT_SYNONYMS = {"sportsbook": "betting", "sports": "betting", "sports betting": "betting", "bet": "betting",
                    "live casino": "casino", "slots": "casino"}


def bonus_terms_tables(doc: Doc) -> list:
    return [t for t in doc.tables if t.col("journey") >= 0 and t.col("wagering") >= 0
            and t.col("deposit_conditional", "deposit conditional") >= 0 and t.col("product") >= 0]


def check_bonus_rules(doc: Doc, rep: Report, markets: list, mdata: dict, journeys: dict) -> None:
    rows = mdata.get("markets", {})
    ruled = []
    for mk in markets:
        row = rows.get(market_code(mk))
        if not row:
            continue
        br = row["bonus_rules"]
        if br["max_wagering_multiplier"] is not None or br["single_product"] or br["first_play_only"] \
                or br["deposit_conditional_allowed"] is False:
            ruled.append((market_code(mk), row))
    if not ruled:
        return
    bonus_jids = []
    for jid, j in journeys.items():
        if jtype(jid) not in ("MKT", "VIP"):
            continue
        texts = []
        if j["spec"]:
            texts.extend(dim(j["spec"], k)[0] for k in ("email_purpose", "flow_steps", "branch_logic"))
        for t in j["flows"]:
            for (_ln, cells) in t.rows:
                texts.extend(cells[c] for c in (t.col("purpose"), t.col("subject")) if 0 <= c < len(cells))
        if is_offer(" ".join(texts)):
            bonus_jids.append((jid, j.get("spec_line", j["line"])))
    tables = bonus_terms_tables(doc)
    listed = set()
    for t in tables:
        ji, mi, pi = t.col("journey"), t.col("market"), t.col("product")
        wi, di, fi = t.col("wagering"), t.col("deposit_conditional", "deposit conditional"), t.col("first_play", "first play")
        for (ln, cells) in t.rows:
            def cell(i):
                return norm(cells[i]) if 0 <= i < len(cells) else ""
            jm = re.search(r"JRN_[A-Za-z0-9_]+|(?:MKT|VIP)_\d{2}", cells[ji] if ji < len(cells) else "")
            if jm:
                listed.add(jm.group(0))
            mcode = market_code(cell(mi)) if mi >= 0 and cell(mi) else ""
            for (code, row) in ruled:
                if mcode and mcode not in (code, "ALL"):
                    continue
                br = row["bonus_rules"]
                mx = br["max_wagering_multiplier"]
                wtxt = cell(wi)
                wm = re.search(r"\d+", wtxt)
                no_wagering = wtxt in ("none", "no wagering", "n/a", "-") or wtxt.startswith("no wagering")
                if mx is not None and not no_wagering and (not wm or int(wm.group(0)) > mx):
                    rep.error(ln, "C26", "%s: wagering_multiplier '%s' exceeds %dx (markets.json bonus_rules)" % (code, cell(wi), mx))
                if br["single_product"]:
                    prods = [PRODUCT_SYNONYMS.get(p, p) for p in re.split(r"\s*(?:\+|,|/|&|\band\b)\s*", cell(pi)) if p]
                    prods = list(dict.fromkeys(prods))
                    allowed = set(row["consent"].get("products") or []) | {"poker"}
                    if len(prods) != 1 or (prods[0] not in allowed and prods[0] != "none"):
                        rep.error(ln, "C26", "%s: bonus_product '%s' must be exactly one product of %s (single-product rule)"
                                  % (code, cell(pi), ", ".join(sorted(allowed))))
                if br["first_play_only"] and cell(fi) not in ("yes", "true"):
                    rep.error(ln, "C26", "%s: first_play_only must be 'yes' (bonus only at the first play occasion)" % code)
                if br["deposit_conditional_allowed"] is False and cell(di) not in ("no", "false"):
                    rep.error(ln, "C26", "%s: deposit_conditional must be 'no' (no deposit-conditional reward)" % code)
    for (jid, ln) in bonus_jids:
        short = re.sub(r"^JRN_((?:MKT|VIP)_\d{2}).*$", r"\1", jid)
        if jid not in listed and short not in listed:
            rep.error(ln, "C26", "journey %s offers a bonus in %s but has no row in a Bonus terms table (columns Journey, "
                      "Market, bonus_product, wagering_multiplier, deposit_conditional, first_play_only)"
                      % (jid, ", ".join(c for (c, _r) in ruled)))


def block_covers(text: str) -> bool:
    low = text.lower()
    return bool(re.search(r"disclosure|helpline|footer", low)) and \
        bool(re.search(r"register|suppression|self-exclusion", low)) and \
        bool(re.search(r"\brg\b|responsible|safer gambling", low))


def check_enums(doc: Doc, rep: Report) -> None:
    for m in ENUM_RE.finditer(doc.text):
        attr, op, raw = m.group(1), m.group(2).lower(), m.group(3)
        if op in ("is", "is not", "changes to") and raw[:1] not in "\"'":
            # prose such as "rg_risk_level is evaluated": only quoted values are checked
            continue
        if raw[:1] in "[(\"'":
            values = re.findall(r"[\"']([^\"']*)[\"']", raw)
            if not values and raw[:1] in "[(":
                values = [v.strip() for v in raw.strip("[]()").split(",") if v.strip()]
        else:
            values = [v.strip() for v in raw.split(",")]
        for v in values:
            if v.lower() in ("and", "or", "not", "true", "false") or v == "":
                if v.lower() in ("true", "false"):
                    rep.error(line_of(doc, m.start()), "C19", "%s compared to boolean '%s'" % (attr, v))
                continue
            if v not in ENUMS[attr]:
                rep.error(line_of(doc, m.start()), "C19", "%s value '%s' is not in the enum (%s)" % (attr, v, ", ".join(sorted(ENUMS[attr]))))


def check_gate(doc: Doc, rep: Report, mode: str, spans: dict) -> None:
    text, where = doc.text, "document"
    if mode == "blueprint" and 4 in spans:
        a, b = spans[4]
        text, where = "\n".join(doc.lines[a - 1:b]), "section 5"
    missing = [name for (name, pat) in GATE_TERMS if not re.search(pat, text, re.I)]
    if missing:
        rep.error(1, "C20", "gate in %s is missing: %s" % (where, ", ".join(missing)))


def check_audit(doc: Doc, rep: Report) -> None:
    want = ["priority", "area", "finding", "risk", "fix"]
    tables = [t for t in doc.tables if all(any(w == h or h.startswith(w) for h in t.header) for w in want)]
    if not tables:
        rep.error(1, "C21", "no audit findings table with columns Priority, Area, Finding, Risk, Fix")
        return
    for t in tables:
        ri = t.col("risk")
        last = -1
        for (ln, cells) in t.rows:
            risk = norm(cells[ri]) if ri < len(cells) else ""
            if risk not in RISK_ORDER:
                rep.error(ln, "C21", "risk '%s' is not one of %s" % (risk, ", ".join(RISK_ORDER)))
                continue
            rank = RISK_ORDER.index(risk)
            if rank < last:
                rep.error(ln, "C21", "row out of order: '%s' after a lower-risk row" % risk)
            last = max(last, rank)


LEDGER_ROLES = ["compliance & rg officer", "crm manager", "backend engineer", "fraud & aml analyst"]
LEDGER_LABEL_RE = re.compile(r"^[PX][1-9]\d*$")
LEDGER_BLOCK_RE = re.compile(r"^###\s+([PX][1-9]\d*)\b")
LEDGER_FIELD_RE = re.compile(r"^[-*]\s+(?:\*\*)?([A-Za-z][A-Za-z ]*?):(?:\*\*)?(?:\s+(.*))?$")


def ledger_blocks(doc: Doc) -> list:
    """Return (line, label, fields) for each '### P<n>' / '### X<n>' block; fields map name -> text."""
    out = []
    heads = [(i, lvl) for (i, lvl, _t) in doc.headings]
    for (i, lvl, title) in doc.headings:
        m = LEDGER_BLOCK_RE.match("#" * lvl + " " + title)
        if lvl != 3 or not m:
            continue
        end = next((j for (j, l2) in heads if j > i and l2 <= 3), len(doc.lines))
        fields, cur = {}, None
        for k in range(i + 1, end):
            ln = doc.lines[k]
            fm = None if doc.in_fence[k] else LEDGER_FIELD_RE.match(ln)
            if fm:
                cur = fm.group(1).strip().lower()
                fields[cur] = (fm.group(2) or "").strip()
            elif cur is not None and ln.strip() and (doc.in_fence[k] or ln[:1] in (" ", "\t")):
                fields[cur] = (fields[cur] + "\n" + ln.strip()).strip()
        out.append((i + 1, m.group(1), fields))
    return out


def check_ledger(doc: Doc, rep: Report) -> None:
    want = ["priority", "area", "finding", "risk", "fix"]
    tables = [t for t in doc.tables
              if all(any(w == h or h.startswith(w) for h in t.header) for w in want) and t.col("owner") >= 0]
    blocks = ledger_blocks(doc)
    if not tables and not blocks:
        return
    rows = {}
    for t in tables:
        pi, oi, fi, ri = t.col("priority"), t.col("owner"), t.col("fix"), t.col("risk")
        prefix = None
        for (ln, cells) in t.rows:
            cell = lambda c: norm(cells[c]) if 0 <= c < len(cells) else ""
            label = cells[pi].strip().strip("`*").strip() if pi < len(cells) else ""
            if not LEDGER_LABEL_RE.match(label):
                rep.error(ln, "C30", "Priority '%s' is not a P<n> or X<n> label" % label)
            else:
                if prefix and label[0] != prefix:
                    rep.error(ln, "C30", "label %s mixes P and X labels in one table" % label)
                prefix = prefix or label[0]
                if label in rows:
                    rep.error(ln, "C30", "label %s is used twice" % label)
                rows[label] = (ln, cell(ri), cell(oi))
            if cell(oi) not in LEDGER_ROLES:
                rep.error(ln, "C30", "owner '%s' is not one of: Compliance & RG Officer, CRM Manager, "
                                     "Backend Engineer, Fraud & AML Analyst" % cell(oi))
            if cell(fi) in ("", "-", "n/a"):
                rep.error(ln, "C30", "Fix is empty")
    seen = set()
    for (ln, label, f) in blocks:
        if label in seen:
            rep.error(ln, "C30", "finding block %s appears twice" % label)
        seen.add(label)
        risk, owner = norm(f.get("risk", "")), norm(f.get("owner", ""))
        if risk not in RISK_ORDER:
            rep.error(ln, "C30", "block %s: Risk '%s' is not one of %s" % (label, risk, ", ".join(RISK_ORDER)))
        if owner not in LEDGER_ROLES:
            rep.error(ln, "C30", "block %s: Owner '%s' is not one of the four roles" % (label, owner))
        for name in ("fix", "verify"):
            if norm(f.get(name, "")) in ("", "-", "n/a", "null"):
                rep.error(ln, "C30", "block %s: %s is missing or empty" % (label, name.capitalize()))
        if "agent task" not in f:
            rep.error(ln, "C30", "block %s: no Agent task line (write null when it is not an API task)" % label)
        else:
            task = f["agent task"]
            if norm(task) != "null" and not ("dry_run" in task and re.search(r"approv", task, re.I)):
                rep.error(ln, "C30", "block %s: Agent task must be null or ask for dry_run and approval" % label)
        if label in rows:
            if rows[label][1] in RISK_ORDER and risk in RISK_ORDER and rows[label][1] != risk:
                rep.error(ln, "C30", "block %s: Risk differs from its table row" % label)
            if rows[label][2] in LEDGER_ROLES and owner in LEDGER_ROLES and rows[label][2] != owner:
                rep.error(ln, "C30", "block %s: Owner differs from its table row" % label)
        elif tables:
            rep.error(ln, "C30", "block %s has no row in a findings table" % label)
    for label, (ln, _r, _o) in rows.items():
        if label not in seen:
            rep.error(ln, "C30", "label %s has no '### %s' finding block" % (label, label))


def check_forbidden(doc: Doc, rep: Report, forbid: list, operator: str) -> None:
    def compact(s: str) -> str:
        return re.sub(r"[\s\-_.]", "", s).lower()
    op = compact(operator) if operator else ""
    for name in forbid:
        cname = compact(name)
        if not cname or (op and cname == op):
            continue
        for i, ln in enumerate(doc.lines):
            cl = compact(ln)
            if op:
                cl = cl.replace(op, "")
            if cname in cl:
                rep.error(i + 1, "C01", "forbidden name '%s' appears" % name)


def check_placeholders(doc: Doc, rep: Report) -> None:
    for i, ln in enumerate(doc.lines):
        text = ln.replace(VERIFY_MARKER, "")
        spans = []  # report each piece of text once, by its first (most specific) match

        def fresh(m) -> bool:
            if any(a <= m.start() and m.end() <= b for (a, b) in spans):
                return False
            spans.append((m.start(), m.end()))
            return True

        for (rx, label) in PLACEHOLDER_RES:
            for m in rx.finditer(text):
                if fresh(m):
                    rep.error(i + 1, "C02", "placeholder: %s '%s'" % (label, m.group(0)[:40]))
        for m in SLOT_RE.finditer(text):
            if not m.group(1).startswith(("SEG_", "JRN_")) and fresh(m):
                rep.error(i + 1, "C02", "unfilled slot [%s]" % m.group(1))


def check_attributes(doc: Doc, rep: Report, mode: str, journeys: dict, segdefs: list) -> None:
    known = set()
    if mode == "blueprint":
        for t in doc.tables:
            if t.col("attribute") == 0 and t.col("type") >= 0:
                for (_ln, cells) in t.rows:
                    known.update(re.findall(r"[a-z][a-z0-9_]*", cells[0].strip("`")))
    if not known:
        known = ref_tokens(REF_DATA_MODEL)
    if not known:
        return
    cands = []
    for j in journeys.values():
        if j["spec"]:
            for k in ("entry_conditions", "exit_conditions"):
                val, ln = dim(j["spec"], k)
                cands.append((ln, val))
    cands.extend((ln, logic) for (ln, _s, logic) in segdefs)
    reported = set()
    for (ln, text) in cands:
        for m in ATTR_COND_RE.finditer(text or ""):
            tok = m.group(1)
            if tok not in known and tok not in reported:
                reported.add(tok)
                rep.warn(ln, "C17", "attribute '%s' is not defined in the %s" % (
                    tok, "output schema" if mode == "blueprint" else "data-model reference"))


def check_events(doc: Doc, rep: Report, mode: str, journeys: dict, extra: set) -> None:
    known = ref_tokens(REF_EVENTS) | extra
    if mode == "blueprint":
        for t in doc.tables:
            if t.col("event") == 0 and (t.col("fires") >= 0 or t.col("payload") >= 0 or t.col("required") >= 0):
                for (_ln, cells) in t.rows:
                    known.update(re.findall(r"[a-z][a-z0-9_]*", cells[0].strip("`")))
    attrs = ref_tokens(REF_DATA_MODEL)
    if not known:
        return
    reported = set()
    for jid, j in journeys.items():
        if not j["spec"]:
            continue
        for k in ("trigger", "conversion_event"):
            val, ln = dim(j["spec"], k)
            for span in re.findall(r"`([^`]+)`", val):
                span = span.strip()
                if SNAKE_RE.match(span) and span not in attrs and span not in known and span not in reported:
                    reported.add(span)
                    rep.warn(ln, "C18", "journey %s: event '%s' is not in the taxonomy or --events" % (jid, span))


# ---------------------------------------------------------------- main

def run(text: str, path: str, args, mdata: dict = None) -> Report:
    rep = Report(path)
    doc = Doc(text)
    mode, piece = args.mode, args.piece
    extra = set()
    if args.events:
        extra = {l.strip() for l in Path(args.events).read_text(encoding="utf-8").splitlines() if l.strip()}
    check_forbidden(doc, rep, args.forbid or [], args.operator or "")
    check_placeholders(doc, rep)
    journeys = check_journeys(doc, rep, mode, piece, ref_tokens(REF_EVENTS) | extra)
    if mode == "blueprint" or (mode == "flow" and piece == "journey"):
        check_journey_ids(doc, rep)
    segdefs = check_segments(doc, rep, mode, piece)
    check_liquid(doc, rep)
    check_fences(doc, rep)
    check_waits(doc, rep, journeys)
    check_attr_compare(doc, rep, journeys, segdefs)
    spans = {}
    if mode == "blueprint":
        spans = check_sections(doc, rep)
        check_priority(doc, rep)
    check_caps(doc, rep, required=(mode == "blueprint" or (mode == "flow" and piece == "caps")))
    check_notice(doc, rep)
    if args.markets:
        markets = [m.strip() for m in args.markets.split(",") if m.strip()]
        check_markets(doc, rep, markets, mdata)
        if mdata:
            check_market_freshness(rep, markets, mdata, datetime.date.today())
            check_market_status(doc, rep, markets, mdata)
            check_bonus_rules(doc, rep, markets, mdata, journeys)
    check_attributes(doc, rep, mode, journeys, segdefs)
    if mode == "blueprint" or (mode == "flow" and piece == "journey"):
        check_events(doc, rep, mode, journeys, extra)
    check_enums(doc, rep)
    if mode == "blueprint" or (mode == "flow" and piece == "gate"):
        check_gate(doc, rep, mode, spans)
    if mode == "audit":
        check_audit(doc, rep)
        check_ledger(doc, rep)
    return rep


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="deliverable markdown file, or '-' for stdin")
    parser.add_argument("--mode", required=True, choices=["blueprint", "flow", "audit"])
    parser.add_argument("--piece", choices=["journey", "segments", "gate", "rg", "caps"],
                        help="FLOW only: which piece the deliverable is (default journey)")
    parser.add_argument("--markets", help="comma-separated intake markets (GB = UK), enables C16 and C26-C28")
    parser.add_argument("--markets-file", default=str(REF_MARKETS),
                        help="market facts JSON (default: the bundled references/markets.json)")
    parser.add_argument("--operator", help="operator name supplied by the user; exempt from C01")
    parser.add_argument("--forbid", action="append", metavar="NAME",
                        help="client or source-operator name that must not appear (repeatable)")
    parser.add_argument("--events", help="file of extra operator event names, one per line (C18)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args()

    if args.piece and args.mode != "flow":
        print("error: --piece is only valid with --mode flow", file=sys.stderr)
        return 2
    if args.mode == "flow" and not args.piece:
        args.piece = "journey"
    if args.events and not Path(args.events).is_file():
        print("error: --events file not found: %s" % args.events, file=sys.stderr)
        return 2
    try:
        if args.file == "-":
            text, path = sys.stdin.read(), "<stdin>"
        else:
            p = Path(args.file)
            text, path = p.read_text(encoding="utf-8"), args.file
    except (OSError, UnicodeDecodeError) as exc:
        print("error: cannot read %s: %s" % (args.file, exc), file=sys.stderr)
        return 2

    mdata = None
    if args.markets:
        try:
            mdata = load_markets(Path(args.markets_file))
        except MarketsError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
    rep = run(text, path, args, mdata)
    items = sorted(rep.items, key=lambda f: (f["line"], f["rule"]))
    errors = [f for f in items if f["level"] == "ERROR"]
    warns = [f for f in items if f["level"] == "WARN"]
    if args.json:
        print(json.dumps(items, indent=2))
    else:
        for f in items:
            print("%s:%d: %s [%s] %s" % (f["file"], f["line"], f["rule"], f["level"], f["message"]))
        print("\n%d error(s), %d warning(s)" % (len(errors), len(warns)))
    failed = bool(errors) or (args.strict and bool(warns))
    if not failed and not args.json:
        print("clean. Next: run the judgement pass, confirm the notice line, and deliver "
              "(protocols/self-check.md steps 4-7).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

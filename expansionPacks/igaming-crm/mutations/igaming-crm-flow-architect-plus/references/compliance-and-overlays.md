# Compliance baseline and market overlays

Context: the compliance minimums every design meets, the licence-posture
choice, the market overlay template, how overlays are rendered from
`references/markets.json`, and how to handle markets not in that file. Read it
at intake step 4, for Appendix A of a blueprint, and for every FLOW piece with
named markets.

## Contents
- Key idea
- Compliance minimums
- Message-type separation
- Universal marketing suppression
- Data protection baseline (EU)
- Licence posture
- Overlay template
- Rendering an overlay from markets.json
- Closed-pending markets (market-status banner)
- Markets not in markets.json

## Key idea
There is no single gambling law. A design applies a common baseline, then one
overlay per market routed by `regulatory_zone`, in one workspace with zone
branches (separate workspaces only for separate brands with different
products). Market facts (register, real-time check, consent, bonus rules, time
windows, helpline, source, verification date and status) live only in
`references/markets.json`; this file says how to use them.

## Compliance minimums
- Marketing consent is explicit, unbundled from terms acceptance, informed,
  given by a clear affirmative action (no pre-ticked boxes), and as easy to
  withdraw as to give. Records keep timestamp, source and policy version.
- Transactional, service and RG messages need no marketing consent and carry
  no promotional content.
- Self-exclusion suppression takes effect within 5 minutes.
- Bonuses are suppressed for RG risk medium and above.
- Every promotional email carries an 18+ notice, a safer-gambling message and
  link, and the market's helpline.
- VIP status never overrides RG suppression.
- No message encourages a limit-setter to raise a limit; no loss-chasing.

## Message-type separation
| Type | Examples | Consent | Suppression |
|---|---|---|---|
| Transactional | Verification, KYC, withdrawal confirmation, password reset | Not required | Closed accounts only |
| Promotional | Bonuses, free spins, reloads, newsletters | Required | Full gate |
| Responsible gambling | Risk alerts, limit nudges, safer-play tools, SE information | Not required | Never suppressed by marketing rules |
| System | Unsubscribe confirmation, preference updates, sunset | Not required | Closed accounts only |

## Universal marketing suppression
Never send marketing to: self-excluded players (including register matches),
active timeouts, unverified age (`age_verified != true`), unverified KYC where
KYC is required before marketing, AML-restricted, RG high or severe,
globally unsubscribed, unlicensed jurisdictions (`country_license_status !=
"licensed"`), suspended or closed accounts.

## Data protection baseline (EU)
- Lawful basis: consent for promotional email; contract or legitimate
  interest for transactional email.
- Erasure propagates to the CRM within the agreed SLA; retention periods are
  defined and enforced; only attributes needed for a stated purpose are held.
- International transfers to the CRM vendor are covered by the vendor's data
  processing agreement and transfer mechanism (legal question bank, data
  protection category).

## Licence posture
| Licence type | Approach |
|---|---|
| EU national licence | Mandatory national register checks (5-minute SLA, before marketing and play); statutory RG and bonus limits; KYC before real-money play; licence footer per regulator |
| Offshore licence | No national register: the internal self-exclusion database carries the full burden, so L4 and reconciliation are non-negotiable; risk-based KYC with clear thresholds; strong internal RG model; cross-border targeting of regulated markets is a legal question, not a default |
Intake records the posture; the overlay baseline follows from it.

## Overlay template
Each market block states five things, under a heading naming the market:
1. Journey modifications (journeys added, removed or altered for the zone).
2. Suppression rules, including the national register and its integration.
3. Mandatory disclosures: helpline, licence footer, age notice, language.
4. RG requirements (limits, reality checks, statutory interventions).
5. Bonus rules (allowed offers, first-play or single-product rules, wagering
   disclosure).
Implementation: `regulatory_zone == "<code>"` branches in journeys and the
zone footer snippet; register matches set `self_exclusion_register_match`.

## Rendering an overlay from markets.json
1. Look the market up by code (`UK`, `DE`, `SE`, `ES`, `IT`, `NL`, `DK`, `ON`,
   `BR`, `MX`, `GR`, `MT`, `REST_OF_EU`; `GB` means `UK`); the validator also
   accepts the row's full name ("Brazil", "United Kingdom", "Great Britain")
   and warns when a market has no row.
2. Render the five template points from the row: `register` and `api_check`
   into point 2, `helpline` into point 3, `time_windows` and `notes` into
   point 4, `bonus_rules` into point 5, `consent` into point 1 when
   `per_product_per_channel` is true (UK: every email checks the
   `consent_<product>_<channel>` attribute for its product and channel).
3. Marker: a row whose `status` is not `primary` carries "(verify before
   deployment)" on its overlay block and helpline line; a `primary` row still
   marks every field listed in `unverified_fields` (validator rule C16).
4. Bonus journeys add a Bonus terms table (columns Journey, Email, Market,
   bonus_product, wagering_multiplier, deposit_conditional, first_play_only);
   the validator checks each row against the market's `bonus_rules` (C26).
   `bonus_product` vocabulary: betting (also written sportsbook or sports),
   casino (also live casino), bingo, poker, or `none` for a content-only
   variant; a no-wagering bonus writes `0` or `none` as wagering_multiplier.
5. A `verified_on` older than `stale_after_days` (180) is flagged C27: tell
   the user the row needs re-verification; it does not block delivery.

## Closed-pending markets (market-status banner)
A row with `market_status: closed_pending` (currently BR) is not refused. The
skill still designs that market's flows, and:
1. The first line of the deliverable is the row's `banner` text, for example
   "MARKET STATUS: BR closed pending MP 1.394/2026 (25 Sep 2026); licences
   end ~25 Oct 2026. Counsel must confirm legal status before any send."
2. The market's overlay block repeats the status note.
3. Hold mechanism: until counsel confirms in writing (LQ_LIC_05), the
   backend sets `country_license_status = "pending"` for every player in
   that zone. The gate condition `country_license_status == "licensed"` in
   `SEG_CAN_RECEIVE_MARKETING` (and L4) then blocks every marketing send while
   the journeys stay built; counsel's confirmation flips the value to
   `"licensed"`, a refusal to `"unlicensed"`. Never invent a separate approval
   attribute.
4. The validator warns (C28) and fails only when the banner is missing.
5. Service and RG flows for that market are unaffected.

Example rendered from the DE row (status secondary, so every fact is marked):
- Journey modifications: zone branch on `regulatory_zone == "DE"`; German-language templates.
- Suppression and register: OASIS match sets `self_exclusion_register_match = true`, 5-minute SLA (verify before deployment).
- Disclosures: helpline BIÖG (formerly BZgA) 0800 1372700 (verify before deployment); licence footer from Customer.io Snippets; 18+ notice.
- RG requirements: LUGAS cross-operator deposit limit stored as `lugas_limit_eur`; never prompt a raise (verify before deployment).
- Bonus rules: no shipped fact; LQ_LIC_04 and the stated assumption.

## Markets not in markets.json
Any market without a row (other LatAm, Africa, other North America,
Asia-Pacific countries) has no shipped overlay. For each such market:
1. Ask the user for the licence held for that market, the register (if any),
   the helpline and any bonus or advertising rules they already know.
2. If they cannot answer, write the overlay block with explicit assumptions
   (for example "Assumption: no national register; internal SE database
   applies; helpline to be confirmed by counsel") and list the legal question
   IDs that must be answered: LQ_LIC_01 to LQ_LIC_04, LQ_CON_01, LQ_RG_02,
   plus LQ_CRY_01 to LQ_CRY_03 for crypto operators and LQ_MIX_01 to
   LQ_MIX_03 for esports.
3. Never present an assumed helpline number or register name as fact.
4. Unanswered questions follow the rule in the legal question bank: an
   explicit, flagged assumption for each; only LQ_LIC_01 defaults to blocking
   marketing in that market ("blocked pending LQ_LIC_01").

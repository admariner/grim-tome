# Legal and compliance question bank

Context: questions counsel must answer before launch, by category, each with
why it matters and the recommended action if the answer is unclear. Read it
for blueprint section 17, for markets without a shipped overlay, and when an
audit finds an obligation the design cannot settle.

## Contents
- How to use
- Licensing and jurisdiction
- Marketing consent
- Data protection
- Responsible gambling
- Email content
- VIP and loyalty
- Self-exclusion and SLAs
- Technical gates
- Crypto payments (optional)
- Esports and mixed verticals (optional)

## How to use
Copy the relevant rows into the deliverable with their IDs, adapted to the
operator's licence and markets. Optional categories apply only when the
operator offers crypto payments (LQ_CRY_*) or esports betting (LQ_MIX_*);
intake asks about both.

Rule for a question counsel has not answered yet:
1. State an explicit assumption in the deliverable's assumptions list and in
   the market overlay, AND flag the question ID as open next to it (for
   example "Assumption: soft opt-in not used; open: LQ_CON_01").
2. Apply the "action if unclear" column where it shapes the design without
   blocking it (terms in every bonus email, explicit opt-in, no prize draws).
3. LQ_LIC_01 is the one blocking default: until counsel confirms the licence
   permits marketing to a market, that market's players carry
   `country_license_status = "unlicensed"`, so the gate blocks all marketing
   there. Design the market's journeys in full anyway and mark them
   "blocked pending LQ_LIC_01"; service and RG messages are unaffected.

## Licensing and jurisdiction
| ID | Question | Why it matters | Action if unclear |
|---|---|---|---|
| LQ_LIC_01 | Does the operator's licence permit marketing to residents of each target market where it holds no local licence? | Cross-border solicitation into regulated markets risks enforcement, payment blocks and blacklisting | Set `country_license_status != "licensed"` for those markets, so the gate blocks marketing |
| LQ_LIC_02 | Which footer disclosures does the licensing authority require in promotional email? | Missing licence details can breach licence terms and provider policies | Footer from Customer.io Snippets: entity, licence number, authority, address, 18+ |
| LQ_LIC_03 | How are players handled who move to, or connect from, blocked or sanctioned jurisdictions? | Marketing or play from sanctioned territories breaches AML and licence covenants | Country change triggers a compliance review and sets `country_license_status`; marketing blocked until cleared |
| LQ_LIC_04 | What bonus, inducement and advertising restrictions apply in each target market? | Many markets cap or ban bonuses, free spins or VIP incentives | Apply the market's `bonus_rules` from `references/markets.json`; content-only variants where it has none, until answered |
| LQ_LIC_05 | For a market whose `market_status` is `closed_pending` (BR), may any marketing be sent, and from when? | Licences may lapse while flows are live | Produce the flows with the market-status banner; no send until counsel confirms in writing |
| LQ_LIC_06 | UK: may separate betting and casino offers share one email for a player opted in to both? | Unconfirmed reading of the 19 Jan 2026 single-product rule (verify before deployment) | One product per email until answered |

## Marketing consent
| ID | Question | Why it matters | Action if unclear |
|---|---|---|---|
| LQ_CON_01 | Is explicit unbundled opt-in required for email and SMS marketing in each market, or is soft opt-in permitted for customers (UK position unconfirmed; verify before deployment)? | Invalid consent removes the lawful basis for all marketing | Explicit, unticked, unbundled opt-in everywhere; UK per product and per channel |
| LQ_CON_02 | What consent evidence must be stored and for how long? | The operator carries the burden of proof | Store timestamp, source, version and topic for every change |
| LQ_CON_03 | May transactional onboarding mention any offer for a player without marketing consent? | Mixing service and promotion breaches anti-spam rules | Never; transactional templates carry no offers |

## Data protection
| ID | Question | Why it matters | Action if unclear |
|---|---|---|---|
| LQ_DP_01 | Is the transfer of behavioural and payment data to the CRM vendor covered by a valid transfer mechanism and processing agreement? | Unlawful transfers create regulatory exposure | Execute the vendor's processing agreement and transfer clauses before go-live |
| LQ_DP_02 | What retention and erasure schedule applies to CRM profiles and event history after closure or an erasure request? | Over-retention breaches data minimisation | Erase or anonymise within 30 days of a verified request, keeping only legally required records |
| LQ_DP_03 | Is gambling behaviour data treated as special-category or otherwise sensitive data in any target market? | Higher-risk processing may need extra safeguards or a basis | Treat as confidential; no sharing with ad networks; minimise attributes |

## Responsible gambling
| ID | Question | Why it matters | Action if unclear |
|---|---|---|---|
| LQ_RG_01 | What is the operator's liability if a self-excluded player receives marketing through a technical delay? | Duty of care failures are treated severely | `RG_EXIT_BLOCK` plus the L4 synchronous check, 5-minute SLA, reconciliation, audit log |
| LQ_RG_02 | Which helplines, RG bodies and disclosures are required per market? | Disclosures differ per regulator | Zone helpline snippet with values marked for verification |
| LQ_RG_03 | Which interventions are mandatory when risk indicators appear (loss velocity, overnight play)? | Failing to intervene can be treated as predatory | RG_12 with the shipped signal and action tables |

## Email content
| ID | Question | Why it matters | Action if unclear |
|---|---|---|---|
| LQ_EC_01 | Does any planned content risk being read as loss-chasing or misleading? | Advertising codes prohibit both | Content rubric review on every template |
| LQ_EC_02 | Must wagering requirements and key terms appear in the email itself? | Hidden material terms are a consumer-protection issue | Terms summary in every bonus email |
| LQ_EC_03 | Could brand imagery or tone appeal to minors? | Advertising to minors is prohibited everywhere | Adult tone; 18+ notice; no youth-oriented channels |

## VIP and loyalty
| ID | Question | Why it matters | Action if unclear |
|---|---|---|---|
| LQ_VIP_01 | What due diligence (source of funds or wealth) is required before VIP rewards? | High-value incentives without checks raise AML risk | VIP perks require `kyc_status == "approved"` and completed enhanced checks |
| LQ_VIP_02 | Confirm VIP status can never override RG suppression or cooling-off | Commercial pressure on VIPs is a known failure mode | Hard rule in segments and VIP_11 exits |
| LQ_VIP_03 | Are prize draws or raffles regulated as lotteries or contests in any market? | Unlicensed prize promotions breach local law | No prize-draw promotion in a market until answered |

## Self-exclusion and SLAs
| ID | Question | Why it matters | Action if unclear |
|---|---|---|---|
| LQ_SE_01 | What is the binding SLA from self-exclusion to full suppression? | Delay is a breach of duty of care | 5 minutes end to end |
| LQ_SE_02 | Which audit evidence proves suppression within the SLA? | Investigations need immutable records | Append-only log retained 7 years |
| LQ_SE_03 | What steps apply when an exclusion or timeout ends? | Automatic re-engagement can harm returning players | No automated marketing until a reviewed reactivation and a hold period |

## Technical gates
| ID | Question | Why it matters | Action if unclear |
|---|---|---|---|
| LQ_TG_01 | Is the residual risk of the async variant (no L4) acceptable, and who signs the acceptance? | A send can occur inside the sync window | L4 required; async variant only with written acceptance, flagged |
| LQ_TG_02 | What must happen when the verify endpoint or the CRM API is down? | Outages must not compromise protection | Fail safe: block sends; compliance reviews before re-queue |
| LQ_TG_03 | Must unsubscribes propagate across email, SMS, push and in-app at once? | Fragmented opt-outs breach anti-spam law | One global unsubscribe gates every channel |

## Crypto payments (optional)
| ID | Question | Why it matters | Action if unclear |
|---|---|---|---|
| LQ_CRY_01 | What source-of-funds checks apply before crypto depositors receive bonuses? | Higher AML risk | Bonus eligibility requires approved KYC and wallet screening |
| LQ_CRY_02 | Do crypto-denominated offers fall under financial or crypto-asset marketing rules? | Some markets regulate them separately | Express offers in fiat equivalents with clear terms |
| LQ_CRY_03 | How are wallet addresses classified and stored in the CRM? | Wallets can identify individuals | Do not send wallet addresses to the CRM; use a pseudonymous flag |

## Esports and mixed verticals (optional)
| ID | Question | Why it matters | Action if unclear |
|---|---|---|---|
| LQ_MIX_01 | Does esports marketing risk reaching minors? | Esports audiences skew younger | Esports content only to age-verified players; no youth channels |
| LQ_MIX_02 | Are live in-play promotions with time pressure permitted? | Urgency in live betting raises RG risk | No time-pressure framing; factual fixture information only |
| LQ_MIX_03 | Does cross-vertical profiling need disclosure in the privacy notice? | Undisclosed profiling breaches transparency duties | Disclose cross-product personalisation in the privacy notice |

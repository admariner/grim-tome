# KPIs, A/B testing and the content rubric

Context: KPI families with targets and alert logic, refresh tiers, A/B testing
rules, and the content rubric used by the self-check judgement pass. Read it
for blueprint sections 9, 13 and 14, and at self-check step 4.

## Contents
- Key idea
- KPI families
- Refresh tiers
- A/B testing: approved categories
- A/B testing: prohibited categories
- A/B testing: design standards
- A/B testing: RG constraints
- Quarterly test calendar format
- Content rubric (judgement pass)
- Email content matrix columns

## Key idea
One regulator-grade benchmark exists: the KSA (Netherlands) deposit-limit
evaluation reported in July 2025: players above their limit 9.7% to 2.2%,
average monthly loss EUR 116 to 80, players losing over EUR 1,000 4% to 1%
(secondary press; verify before deployment). Every other target is marked
"assumption, calibrate": an opening value, not a benchmark; replace it with
the operator's own baseline after 4-8 weeks of data. Compliance KPIs with a
target of zero are not calibrated: any non-zero value is an incident. Every
RG success metric is read next to a channelisation / retention guardrail: a
protective metric that improves while licensed-site retention drops signals
displacement to unlicensed sites, not protection.

## KPI families
Each KPI ships with definition, calculation, target, alert threshold and data
source.

| Family | KPI | Calculation | Target | Alert | Source |
|---|---|---|---|---|---|
| Lifecycle | Registration to first deposit (7 d) | unique first depositors within 7 d / registrations | 20%, assumption, calibrate | below 70% of target, 7-day average | Customer.io + warehouse |
| Lifecycle | KYC completion (72 h) | verified within 72 h / KYC requests | 75%, assumption, calibrate | below 60% | KYC provider |
| Lifecycle | Welcome bonus take-up | claimed / eligible first depositors | 60%, assumption, calibrate | below 45% | Bonus service |
| Lifecycle | First to second deposit | players with 2+ deposits in 30 d / first depositors | 35%, assumption, calibrate | below 25% | Payments |
| Lifecycle | Dormant reactivation | reactivated within 14 d / dormant targeted | 5%, assumption, calibrate | below 3% | Campaign analytics |
| Engagement | WAU/MAU | weekly actives / monthly actives | 40%, assumption, calibrate | below 30% | Game engine |
| Engagement | Cross-sell conversion (30 d) | converted / targeted single-vertical | 10%, assumption, calibrate | below 6% | Warehouse |
| Engagement | VIP upward migration (90 d) | upgraded / eligible tier base | 10%, assumption, calibrate | below 5% | Loyalty service |
| Engagement | Click-to-open rate | unique clicks / unique opens | 15%, assumption, calibrate | below 10% | Customer.io |
| RG | Intervention response | engaged / flagged medium-plus players | 60%, assumption, calibrate | below 45% | RG service |
| RG guardrail | Retention of intervened players | flagged players still active on the licensed site at 30 and 90 d / flagged players, read against the market's channelisation estimate | monitor against baseline | falls while intervention response rises | Warehouse |
| RG | SE SLA compliance | exclusions suppressed within 5 min / all | 100% | below 100% | Audit log |
| RG | Limit-reduction ratio | players lowering limits / nudged | 10%, assumption, calibrate | below 5% | Account service |
| RG guardrail | Retention of limit-setters | limit-setters and nudged players still active on the licensed site at 30 and 90 d / limit-setters and nudged players, read against the channelisation estimate | monitor against baseline | falls while limit reductions rise | Warehouse |
| RG | Post-timeout re-engagement | safe returns / timeout completers | monitor only | none (never a growth target) | Warehouse |
| RG | RG link click-through | RG link clicks / promotional clicks | 2%, assumption, calibrate | below 1% | Customer.io |
| RG guardrail | Retention of RG-link clickers | clickers still active on the licensed site at 30 and 90 d / clickers, read against the channelisation estimate | monitor against baseline | falls while click-through rises | Warehouse |
| Compliance | Suppression leakage | promotional sends to suppressed profiles | 0 | above 0 is an incident | Send log vs audit log |
| Compliance | Unsubscribe latency | backend update time minus click time | under 30 s | above 120 s | API logs |
| Compliance | Unlicensed-market sends | marketing sends where `country_license_status != "licensed"` | 0 | above 0 is an incident | Send log |
| Compliance | Erasure SLA compliance | erasures completed in SLA / requests | 100% | below 100% | Audit log |
| Compliance | Reconciliation discrepancy | mismatched suppressions / active base | under 0.1% | 0.1% or more | Reconciliation job |
| Deliverability | Inbox placement | inbox / delivered (seed list) | 90%, assumption, calibrate | below 85% | Seed monitor |
| Deliverability | Bounce rate | bounces / sent | under 0.8% | above 1.5% | Customer.io |
| Deliverability | Complaint rate | complaints / delivered | under 0.05% | above 0.1% | Feedback loops |
| Deliverability | SPF/DKIM/DMARC pass | authenticated / sent | 100% | below 100% | DMARC reports |
| Deliverability | Transactional latency | delivery time minus event time | under 10 s | above 30 s | Delivery logs |
| Experimentation | Active tests per month | count | 4, assumption, calibrate | below 2 | Test log |
| Experimentation | Significant win rate | significant / concluded | 30%, assumption, calibrate | below 15% | Test log |
| Experimentation | Incremental lift vs control | (treatment - control) / control | positive, calibrate | negative two months running | Warehouse |
| Experimentation | Holdout size | holdout / active base | 5% | outside 3-8% | Allocation |

## Refresh tiers
- Real time: suppression leakage, SE SLA, bounce and complaint webhooks,
  high-risk RG triggers.
- Hourly: sends, opens, clicks, conversions.
- Daily batch 02:00 UTC: GGR, LTV, cohorts, VIP migration.
- Weekly and monthly: compliance audit reports, erasure verification.

## A/B testing: approved categories
| Category | Example | Primary metric | Secondary |
|---|---|---|---|
| Subject line and preheader | Benefit-led vs curiosity-led | Unique open rate | CTOR, unsubscribe |
| CTA and layout | Text link vs button | Click-through | Conversion |
| Incentive structure and value | Match percentage vs free spins (bonus-eligible only) | Conversion | Bonus cost, RG escalations |
| Send time and cadence | Fixed hour vs engagement-predicted hour | Open within 2 h | Unsubscribe |
| Personalisation and segmentation | Generic vs preference-based block | Conversion | 7-day retention |
Each test records a hypothesis, primary and secondary metrics, segment, and
the decision rule before launch.

## A/B testing: prohibited categories
- Testing RG suppression, or delaying RG, SE or timeout messages.
- Loss-chasing or depleted-balance prompts.
- Omitting wagering or bonus terms in any variant.
- False scarcity, countdown pressure or invented deadlines.
- Testing on unverified, flagged or underage accounts.

## A/B testing: design standards
- Significance 0.05, power 0.80; minimum detectable effect 5% relative for
  conversion, 10% for deposit value.
- Sample size per arm from the two-proportion formula:
  n = (z(1-a/2) * sqrt(2 p(1-p)) + z(1-b) * sqrt(p1(1-p1) + p2(1-p2)))^2 / (p1 - p2)^2.
- Duration 7 to 28 days; a test without significance at 28 days is closed as
  underpowered.
- Holdout of 5-10% receiving no marketing for 30 days to measure incrementality.
- Small segments (for example top VIP tiers) use full-cohort splits, not samples.

## A/B testing: RG constraints
- `rg_risk_level` medium and above is excluded from every promotional variant.
- No aggressive bonus variants to players in cooling-off, with recent limit
  changes, or with problem indicators.
- The gate and topic consent override allocation; a mid-test opt-out is
  logged as attrition for its variant.

## Quarterly test calendar format
| Quarter | Focus | Segment | Hypothesis | Primary metric |
|---|---|---|---|---|
| Q1 | Onboarding | `SEG_NEW_REGISTRANT` | A product tour by preference lifts first deposits versus a generic tour | Registration to first deposit |

## Content rubric (judgement pass)
For each email and each test variant, label `rg_content_check: pass | fail`.
Fail if any of these is true:
1. Loss-chasing: refers to losses, recovering money, "winning it back", or
   targets a recent loss.
2. False urgency: countdowns, "last chance" without a real terms-based end
   date, invented scarcity, pressure to act now.
3. Minors: imagery, language or channels that appeal to under-18s.
4. Limits: encourages raising or removing a limit.
5. Terms: a bonus without wagering requirement, expiry and key conditions.
6. Layer mixing: an offer inside a transactional, service or RG message.
7. Prohibited A/B category (list above).
Fix every fail before delivery; the deliverable may include the labels in the
section 9 content matrix.

## Email content matrix columns
Journey, email number, email purpose, subject approach (a direction such as
"factual reminder", not copy), content type, personalisation fields, offer
type (none, bonus, free spins, reload, free bet), RG requirement (footer,
helpline, safer-play block), compliance notes, rg_content_check.

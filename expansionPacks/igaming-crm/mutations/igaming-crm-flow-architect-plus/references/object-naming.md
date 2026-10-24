# Object naming

Context: every workspace object BUILD creates carries its spec ID, so a re-run
can find it by name and reuse it instead of creating a duplicate. Read it in
BUILD stages 2-8 before each find-by-name, and in LIVE-AUDIT when matching
workspace objects to the libraries.

## Spec ID per object type
| Type (build sheet) | Spec ID pattern | Customer.io name | Where the spec ID lives |
|---|---|---|---|
| `segment` | `SEG_UPPER_SNAKE` (segment library) | exactly the spec ID, for example `SEG_CAN_RECEIVE_MARKETING` | name |
| `automation` | `JRN_<TYPE>_<NN>_<Name>` (journey catalogue) | exactly the spec ID, for example `JRN_MKT_10_Dormant_Reactivation` | name |
| `message_action` | `<journey spec ID>#<step>[-<variant>]`, for example `JRN_MKT_10_Dormant_Reactivation#05` or `...#02-sportsbook` | starts with the step and variant: `05 Email: return offer`, `02-sportsbook Email: what has changed` | name prefix |
| `frequency_cap` | `LIM_<CHANNEL>_<LAYER>_<SCOPE>` (caps reference) | exactly the spec ID, for example `LIM_EMAIL_MKT_STD` | name |
| `webhook_configuration` | `WHK_<PURPOSE>` | exactly the spec ID, for example `WHK_L4_VERIFY_SUPPRESSION` | name |
| `reporting_webhook` | `WHK_<PURPOSE>` | exactly the spec ID, for example `WHK_REPORTING_COUNTER_FEED` | name |
| `snippet` | `SNP_<NAME>` | the snippet's Liquid name, lower snake case: `SNP_RG_URL` is `rg_url` | name, without the `SNP_` prefix |
| `subscription_topic` | `TOP_<ID>` | the player-facing topic name, for example `Casino Offers` | description, which starts with the spec ID |

Topics and snippets are the two exceptions: a topic name is shown to players on
the preference page and a snippet name is referenced from Liquid, so neither
may carry an upper-case code. A topic's description begins with its spec ID
(`TOP_CASINO_OFFERS: casino promotions and bonuses`), and the build sheet's
Notes cell repeats it.

Topic spec IDs: `TOP_CASINO_OFFERS`, `TOP_SPORTSBOOK_OFFERS`,
`TOP_VIP_LOYALTY`, `TOP_PRODUCT_UPDATES`, `TOP_SAFER_GAMBLING`,
`TOP_TRANSACTIONAL` (subscription topics reference).

Frequency caps carry the rules of the caps reference: `LIM_EMAIL_MKT_STD`
(email 1 per 1 day and 4 per 7 days), `LIM_EMAIL_MKT_VIP` (email 1 per 1 day
and 5 per 7 days), `LIM_SMS_MKT_WEEKLY` (SMS 2 per 7 days). An automation
references one cap, so the daily and weekly allowances of a class sit in one
cap as two rules.

Action numbering. The flow-table step number of the design is the action's
number in the workspace and never changes during a build, so a read-back maps
each action to its flow-table row:
- The design's own rows keep their numbers: `03 Wait Until: until IN
  SEG_DORMANT_60, max 35 d`, `05 Email: return offer`.
- Rows the build adds take the number of the email they serve plus a suffix:
  the L4 webhook is `05.1 L4 verify`, its branch `05.2 L4 branch`, the branch's
  own exit `05.3 L4 exit`; a product split before email 02 is `02.0 Product
  split`, and its email variants are `02-casino Email: ...` and
  `02-sportsbook Email: ...`.
- A design that already draws Webhook and Branch rows before an email keeps
  those numbers instead; the suffixes are only for rows the design left
  implied by its Gate code.
Every message action gets a build-sheet row of type `message_action` with this
spec ID, its topic and its `sending_state`.

## Find by name before create
1. List the type with the read endpoint from `references/build-order.md`
   (segments with `size` and `search`, which filter only when `size` is set;
   automations by paging the list, 20 per page, until a page holds fewer than
   20; snippets with `search`; the other types by full list).
2. Match the exact name, case-sensitive, after trimming; for topics, match the
   description prefix; for snippets, the lower-case name.
3. One match: reuse its ID, record state `existing` in the build sheet, and
   compare its definition with the spec. A difference is reported to the user
   as a finding with both versions; it is changed only with the user's
   approval, and an automation's definition only while it is in `draft`.
4. No match: create it (after the stage's dry-run approval) and record state
   `created`.
5. Two or more matches: stop the stage, list them with IDs, and ask which one
   is canonical. Never pick one silently and never delete the others.

## Names never used
- A client, brand or source-operator name, in any object name, description or
  note. Use the operator name only when the user supplied it, and then only in
  descriptions, never in spec IDs.
- Display names that drop the spec ID ("Dormant reactivation"), because a
  re-run could no longer find the object.
- Suffixes such as `_v2`, `_copy` or dates. A changed object keeps its spec ID;
  history lives in the build sheet and the workspace audit log.

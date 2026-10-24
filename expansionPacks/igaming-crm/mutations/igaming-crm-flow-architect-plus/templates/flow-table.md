#### Flow: [[JOURNEY_ID]]

| Step | Action | Wait | Branch condition | Gate | Subject approach | Content purpose | Personalisation | Exit trigger |
|---|---|---|---|---|---|---|---|---|
| 1 | [[ACTION]] | [[WAIT]] | [[BRANCH_OR_DASH]] | [[GATE_CODE]] | [[SUBJECT_APPROACH]] | [[CONTENT_PURPOSE]] | [[FIELDS]] | [[EXIT_TRIGGER_OR_DASH]] |

Action: Email, Wait, Branch, Webhook or Exit. Gate on Email rows: `MKT`
(marketing gate with L4), `BONUS` (MKT plus `SEG_CAN_RECEIVE_BONUS`) or `TXN`
(transactional gate). Every Email row of a MKT or VIP journey has `MKT` or
`BONUS`, and every offer email (bonus, free spins, reload, free bet, cashback)
has `BONUS`. Non-Email rows use `-`. The L4 webhook and its branch are implied
by `MKT` and `BONUS`; drawing them as explicit Webhook and Branch rows before
the email is also valid. Wait cells may be a fixed delay (`48h`) or a
wait-until (`until IN SEG_DORMANT_60, max 35 d`); a wait-until without a fixed
`max` fails validator rule C23. Walk the timing rule in the journey catalogue
before delivery. Number steps 1..n in workflow order with no gaps; in BUILD the
step number becomes the action's name and spec ID, and rows the build adds (L4
webhook and branch, product split) take suffixes instead of renumbering
(object-naming reference). Bonus journeys add a Bonus terms table (Journey, Email,
Market, bonus_product, wagering_multiplier, deposit_conditional,
first_play_only) checked against `references/markets.json` (C26).

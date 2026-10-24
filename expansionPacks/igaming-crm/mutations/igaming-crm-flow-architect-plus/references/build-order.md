# Build order

Context: why BUILD runs in a fixed order, which Customer.io skill each stage
reads before it writes, and the exact resources and endpoint paths confirmed
with `cio_schema`. Read it before BUILD stage 0 and again at the start of each
stage. The steps themselves, with done-when lines, are in `protocols/build.md`.

## Contents
- Why this order
- Stage map
- Readiness pre-flight
- Customer.io skills per stage
- Confirmed resources and endpoints
- Payload shapes that differ by field
- Mechanics to confirm in the workspace
- Settled

## Why this order
Each stage creates only objects whose dependencies already exist, so no write
references an ID that is not there yet, and a stop at any stage leaves a
consistent, inert workspace.
- Attributes come first because every gate condition reads them. A gate
  condition such as `self_excluded != true` on an attribute the backend never
  sends matches every profile, so a missing gate attribute silently turns the
  gate into "everyone". The build stops instead.
- Topics before automations: an automation's `subscription_topic_id` must point
  at a topic that exists, and starting an automation with an invalid topic is
  one of the few things the platform refuses.
- Snippets before templates and webhooks that render them.
- Gate segments before every other segment: lifecycle and trigger segments may
  include the gate, and automations use gate IDs in triggers, preconditions
  and exits.
- Frequency caps before automations, because the automation's global
  settings reference the limit by ID.
- Webhook configurations before automations, because the L4 webhook action
  uses the verify endpoint configuration.
- Automations last, created in draft, with every message action in
  `sending_state: "draft"`, so even an accidental start queues drafts instead
  of sending.

## Stage map
| Stage | Builds or checks | Depends on |
|---|---|---|
| 0 | Workspace choice, auth, `cio_prime`, workspace facts | nothing |
| 0b | Readiness pre-flight (reads only), planned sheet | 0 |
| 1 | Data-model check (attributes and events present) | 0 |
| 2 | Subscription topics | 0, 1 |
| 3 | Snippets | 0 |
| 4 | Gate and suppression segments | 1 |
| 5 | Lifecycle, trigger and cap segments | 4 |
| 6 | Frequency caps | 0 |
| 7 | Webhook configurations and reporting webhooks | 3 |
| 8 | Automations in draft | 2, 4, 5, 6, 7 |
| 8b | Smoke test (`protocols/smoke.md`) | 4, 8 |
| 9 | Build sheet and its validator | 8 |
| 10 | Activation checklist handed to the user | 9 |

## Readiness pre-flight
Stage 0b runs every later stage's gate check before the first write, with GET
reads only, so the user gets the full blocker list in one table instead of
one stop per run. The verdict is per stage; the build still stops at the
first NO-GO stage. Each line becomes `Pre-flight: stage N GO|NO-GO: <reason>`
in the planned build sheet.
| Stage | Gate | Read | NO-GO when |
|---|---|---|---|
| 1 | The 14 gate attributes (`protocols/build.md` stage 1) present, populated on the sample, canonical values (`references/data-model.md`); field-mapping proposals | `GET .../attributes`, one page of `GET .../customers`, up to five `GET .../customers/{customer_id}`, `GET .../attributes_values` | any gate attribute absent, or present only under an unconfirmed operator name; a non-canonical enum (for example `kyc_status` values none, partial, pending, approved) is reported with its proposed transform |
| 2 | Subscription center and topics | `GET /v1/environments/{environment_id}` (`subscription_center_enabled`), `GET .../subscription_topics` (count) | `subscription_center_enabled` is `false` |
| 3 | Snippets access | `GET .../snippets` | the read is refused |
| 4-5 | Data-driven segment allowance against the segments the plan creates | `GET .../settings/workspace` (`data_driven_segments_allotted`, `has_data_driven_segments_addon`, usage where present) | allotment 0 with no add-on, or fewer slots left than planned creates; treat 0 as blocked unless the settings prove otherwise |
| 6 | Channels of the scoped frequency caps | `GET .../frequency_cap_supported_channels` | a marketing channel the design needs is unsupported (its cap and steps go under "Not built"; NO-GO only if no marketing channel is left) |
| 7 | Webhook access | `GET .../webhook_configurations_minimal`, `GET .../webhooks` (never `GET .../webhook_configurations`) | either read returns 403 |
| 8b | Smoke prerequisites | `GET /v1/environments/{environment_id}` (`identifier_type`, `delivery_settings`) | `identifier_type` is `email` (smoke profiles would need an address); report `delivery_settings` either way |
When the user supplies a gate-readiness pack output from a workspace-specific
data-analyst skill, the stage 1 row comes from its table instead of these
reads (mapping and freshness rules: `references/data-packs.md`); every other
row is read live. Every row names the fix and its owner (backend, CRM
operations, account owner). A NO-GO on a stage after the first one is not a reason to skip the
earlier stages; it is the list the user works through before the next run.

## Customer.io skills per stage
Read each with `cio_skills_read` before the stage's first write. Paths are
Customer.io skill paths, not files in this skill.
| Stage | Skills to read | What they settle |
|---|---|---|
| 0-0b | `cio_prime`; the section headings of recipes/diagnosing_workspace_health.md (the whole recipe only in LIVE-AUDIT or when `GET .../health` shows an alert) | Dry-run rule, resource names (automations are `campaigns`, people are `customers`), IDs as strings; whether an alert should pause the build |
| 1 | fly-api/segment_conditions.md (Resolve Names) | Attribute and event names from `GET /attributes` and `GET /event_names`; a never-sent attribute under negation matches everyone |
| 2 | fly-api/subscriptions.md | Topic fields, `opt_in`, assignment to automations and to single message actions (`subscription_topic_messages/update`) |
| 3 | fly-api/content.md (Snippets) | Snippet create body; templates reference snippets as `{{ snippets.name }}` |
| 4-5 | fly-api/segments.md, fly-api/data_driven_segments.md, fly-api/segment_conditions.md | Allowance check before every create, `attribute_change` leaf shape, `one_of`, negation by `inverse` pair, whole-day windows, nesting depth 1 |
| 6 | fly-api/frequency_caps.md, fly-api/message_throttling.md | Named caps replace the legacy workspace limit; rate limits are not caps |
| 7 | fly-api/webhooks.md | Reporting webhooks versus webhook configurations; secrets never in chat |
| 8 | fly-api/automations.md, fly-api/automation_triggers.md, fly-api/automation_filters.md, fly-api/automation_lifecycle.md, fly-api/flow_control.md, fly-api/delays.md, fly-api/await_completion.md | Create flow, `update_type` routing, full edge lists, filter encodings, exit-condition DSL, Wait Until shape, state transitions never sent |
| 8b | fly-api/customers.md, fly-api/segments.md | Profile create and update body, segment membership read; see `protocols/smoke.md` |
| 9 | fly-api/automation_review.md | Read-back checklist for each draft automation |
| 10 | fly-api/automation_lifecycle.md | What the user does to start, and why `backfill` matters |

## Confirmed resources and endpoints
All paths start `/v1/environments/{environment_id}`; IDs are integers passed as
strings. Reads go through `cio_read_api`, writes through `cio_write_api` with
`dry_run` first. `cio_delete_api` is never used.

| Stage | `cio_schema` resource | Read | Write (after approval) |
|---|---|---|---|
| 0 | `environments`, `settings`, `health` | `GET /v1/environments/{environment_id}`, `GET .../settings/workspace`, `GET .../health` | none |
| 0b | the reads of stages 1-8b | listed in "Readiness pre-flight" | none |
| 1 | `attributes`, `customers`, `event_names`, `attributes_values` | `GET .../attributes`, `GET .../customers` (50 per page), `GET .../customers/{customer_id}`, `GET .../event_names`, `GET .../attributes_values` | none |
| 2 | `subscription_topics` | `GET .../subscription_topics` | `POST .../subscription_topics` |
| 3 | `snippets` | `GET .../snippets` (`search`) | `POST .../snippets`; `PUT .../snippets/{id}` only for an approved value change |
| 4-5 | `segments`, `reusable_conditions`, `settings` | `GET .../segments` (`size`, `search`), `GET .../segments/{segment_id}`, `GET .../segments/{segment_id}/status`, `GET .../segments/{segment_id}/count`, `GET .../reusable_conditions`, `GET .../settings/workspace` | `POST .../segments` |
| 6 | `frequency_caps`, `frequency_cap_supported_channels`, `message_limits` | `GET .../frequency_caps`, `GET .../frequency_cap_supported_channels`, `GET .../message_limits` (legacy, read only) | `POST .../frequency_caps` |
| 7 | `webhook_configurations_minimal`, `webhook_configurations`, `webhooks` | `GET .../webhook_configurations_minimal`, `GET .../webhooks` | `POST .../webhook_configurations`, `POST .../webhooks` with `enabled: false` |
| 8 | `campaigns`, `actions`, `subscription_topic_messages` | `GET .../campaigns` (20 per page, `page` 0-based), `GET .../campaigns/{campaign_id}`, `GET .../campaigns/{campaign_id}/validate`, `GET .../actions/{action_id}`, `GET .../subscription_topic_messages/list` | `POST .../campaigns`, `PUT .../campaigns/{campaign_id}` with `update_type` `recipients`, `conversion`, `exit_conditions`, `add_actions`, `global_settings`; `PUT .../subscription_topic_messages/update` for per-action topics |
| 8b | `customers` | `GET .../customers/{customer_id}`, `GET .../customers/{customer_id}/segments` | `POST .../customers`, `PUT .../customers/{customer_id}`, only for `smk-<run>-` IDs (SKILL.md hard rule 9) |
| 9-10 | `campaigns` | `GET .../campaigns/{campaign_id}` for each row | none |

Never read `GET .../webhook_configurations` (it returns decrypted headers,
which hold secrets); the `_minimal` list is enough to find by name.

## Payload shapes that differ by field
Three condition formats exist and are not interchangeable (fly-api
automation_filters.md):
- Segment conditions (`POST .../segments`): `attribute_change` leaves with a
  `to`/`from` pair; negate with the `inverse` pair, never by swapping the
  operator; lists use `one_of` (at most 50 values).
- Automation `trigger` and `global_exit_conditions`: the filter DSL with
  `attribute`, `segment` and `event_name` leaves inside `and`/`or`. No
  `one_of` here: a multi-value exit is one `eq` leaf per value.
- Action `preconditions`, `conditions`, `multi_conditions`: a flat JSON array,
  URL-encoded and then base64-encoded; negate an attribute with a `!`
  operator (`!eq`), because `inverse` is ignored there and stores the opposite
  condition.

`RG_EXIT_BLOCK` as `global_exit_conditions`: exactly one array element, an
`or` group holding one leaf per value, so a single RG signal exits the player
whether the platform combines array elements with AND or with OR. The
journey's own lifecycle exits (for MKT_10: `bet_placed`, `game_played`,
`deposit_successful` as `event_name` leaves) go inside the same `or` group,
never as further array elements.
```json
[
  {"or": [
    {"attribute": {"field": "marketing_blocked", "operator": "eq", "value": "true"}},
    {"attribute": {"field": "self_excluded", "operator": "eq", "value": "true"}},
    {"attribute": {"field": "self_exclusion_register_match", "operator": "eq", "value": "true"}},
    {"attribute": {"field": "timeout_active", "operator": "eq", "value": "true"}},
    {"attribute": {"field": "rg_risk_level", "operator": "eq", "value": "high"}},
    {"attribute": {"field": "rg_risk_level", "operator": "eq", "value": "severe"}},
    {"attribute": {"field": "account_status", "operator": "eq", "value": "suspended"}},
    {"attribute": {"field": "account_status", "operator": "eq", "value": "closed"}},
    {"attribute": {"field": "aml_status", "operator": "eq", "value": "blocked"}},
    {"attribute": {"field": "aml_status", "operator": "eq", "value": "frozen"}},
    {"attribute": {"field": "aml_status", "operator": "eq", "value": "restricted"}},
    {"attribute": {"field": "unsubscribed", "operator": "eq", "value": "true"}},
    {"segment": {"id": 0}}
  ]}
]
```
Replace `0` in the segment leaf with the ID of `SEG_RG_SUPPRESSED` found or
created in stage 4; the build sheet records it. After the read-back, the user
confirms in the app that the exit panel shows one OR group (activation
checklist).

Per-automation write order in stage 8, because several `update_type`s rewrite
their fields from the request:
1. `POST .../campaigns`: event-triggered journeys with `type: "transactional"`
   and `event`; segment-triggered journeys with `type: "none"`.
2. `recipients`: for segment triggers `type: "seg_attr"` with `trigger`,
   `restart_mode` and `restart_min_interval`; for event triggers the full key
   set (`event`, `event_type`, `attribute_filters`, `filters`,
   `restart_min_interval`), with profile conditions only as segment membership
   in `filters`.
3. `conversion` (goal), then `exit_conditions` with
   `exit_on_trigger_or_filter_not_matched`, `exit_on_conversion_matched:
   false` (required by the schema; exit-on-goal is done by putting the goal's
   event inside the `or` group, never by this flag) and the one-element
   `global_exit_conditions` above; never `exit_and_conversion`, which
   overwrites the exits.
4. `add_actions` with every action and the complete edge list in one request;
   every message action `sending_state: "draft"`; every Wait Until
   `exit_type: "continue"` with `delay` > 0 (its Max time); every exiting
   branch to its own new `exit_action`. Action names follow
   `references/object-naming.md` (flow-table step number first).
5. `global_settings`, after a fresh `GET .../campaigns/{campaign_id}`. Send
   the fields the schema lists for this `update_type`: `subscription_topic_id`
   (a string; the default topic, usually Casino Offers; omitting it clears
   the topic), `send_to_unsubscribed: false`, `use_message_limits: true`,
   `frequency_cap_id` (the `LIM_` cap's ID), `frequency_cap_mode` (verify in
   workspace), `use_workspace_message_limits_retry` and
   `message_limits_retry_window_secs` (86400 for marketing; omitting the window
   while echoing the retry flag zeroes it). `message_throttle` is
   pointer-guarded: omit it.
6. Per-message topics. A design whose topic depends on the product (for
   example "Casino Offers; Sportsbook Offers when `preferred_product ==
   "sportsbook"`") gets a true/false branch on `preferred_product eq
   sportsbook` before each content email and one email action per branch.
   Every marketing message action then carries its own topic through
   `PUT .../subscription_topic_messages/update` with
   `{"updates": {"action_ids": [...]}, "subscription_topic_id": ...,
   "send_to_unsubscribed": false}`; actions without an override inherit the
   automation's default topic. A sportsbook email under Casino Offers would
   reach a player who opted out of Sportsbook Offers only.
7. Read back with `GET .../campaigns/{campaign_id}` and
   `GET .../campaigns/{campaign_id}/validate`; the state must read `draft`,
   and each message action's topic must match its build-sheet row.

## Mechanics to confirm in the workspace
These are not settled by the Customer.io skills or the schema; each is marked
"(verify in workspace)" wherever a protocol relies on it, and the build stops
and asks rather than guessing.
- Whether one frequency cap may hold two email rules with different windows
  (daily and weekly). The schema allows a rule list; if the API refuses, stop
  and ask; never drop the weekly rule silently. (verify in workspace)
- The accepted values of `frequency_cap_mode` in `global_settings`. Read it
  from an automation whose limit was set in the UI before sending it.
  (verify in workspace)
- The webhook-action fields that save the L4 response
  (`can_receive_marketing`) into a journey attribute. The branch reads it as
  `attribute_compare` with `field_source: "journey_attribute"`, which is
  documented; the capture fields are not. (verify in workspace)
- Whether subscription topics need the subscription center enabled
  (`subscription_center_enabled` on the environment). If it reads `false`,
  stop stage 2 and ask the user to enable it in the app. Production
  confirmed the pairing: a production workspace read
  `subscription_center_enabled: false`
  and 0 topics. (verify in workspace)
- The meaning of `data_driven_segments_allotted: 0`. Observed, not proven:
  a production workspace reads 0 with `has_data_driven_segments_addon: false` while already
  holding 17 data-driven segments, and a sandbox read of 0 was once taken as
  unlimited; no create has been refused or accepted under it yet. Until one
  is, pre-flight marks stage 4 NO-GO on a 0 and asks the user to confirm the
  plan's segment entitlement; never substitute a manual segment. (verify in
  workspace)
- Webhook access by token. In a production workspace, `GET .../webhooks` and the webhook
  configuration reads returned 403 on a non-admin token; the pre-flight marks
  stage 7 NO-GO and asks for a token with webhook access. (verify in
  workspace)
- The per-action topic read-back: `GET .../subscription_topic_messages/list`
  lists assignments; whether it shows action-level overrides separately from
  the automation topic. (verify in workspace)

## Settled
- Snippets are referenced as `{{ snippets.name }}`, as Customer.io's
  documentation and `references/liquid-patterns.md` say. The Customer.io agent
  recipe (recipes/liquid_syntax.md, "Snippets") shows `{% snippet "name" %}`;
  that recipe line is the discrepancy, not the design layer.
- RG exits no longer depend on how `global_exit_conditions` combines array
  elements: the block is one `or` element.
- Read values of `frequency_cap_mode` seen so far: `no_cap` (automation without
  limits) and `same_as_campaign` (an action inheriting the automation). The
  value that pins a named cap is the open item above.

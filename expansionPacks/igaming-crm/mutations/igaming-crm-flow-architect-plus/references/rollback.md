# Rollback

Context: what the user can safely remove after a BUILD, what must never be
removed, and in which order. The skill never performs a rollback; it writes the
list (`templates/rollback-list.md`) and the user carries it out in the app or
with their own approved tooling. Read it at BUILD stage 9.

## Contents
- Principles
- What can be removed, and how
- What is never removed
- Order
- Checks before each removal

## Principles
- Rollback runs in the reverse of the build order, because the platform refuses
  to delete an object something still references (a segment used by an
  automation, a cap used by a message, a topic assigned to an automation), and
  a forced delete leaves references pointing at nothing.
- Only objects with state `created` in the build sheet are on the list. Objects
  the build found and reused (`existing`) belonged to the workspace before the
  run and stay.
- Archive before delete where the platform offers it: an archive is
  reversible, a delete is not.

## What can be removed, and how
| Type | Safe removal | Notes from the Customer.io skills |
|---|---|---|
| Automation (draft or stopped) | Archive (`update_type: "state"`, `state: "archive"`); delete only if the user wants it gone | `DELETE` is permanent, returns 200 for any ID and removes the reporting history; confirm by reading the state (`archiving`/`archived`), never by the response |
| Automation that a user started | Stop first (`stop`, with `disposition: "abort"` to cancel queued sends), then archive | A stop does not cancel messages already queued unless the disposition says so |
| Data-driven segment | Archive or delete once no automation, broadcast or other segment uses it | Delete is refused while in use; deletion needs an explicit per-segment approval |
| Frequency cap | Delete after detaching it from every message (`GET .../frequency_caps/{id}/usage`) | A cap in use returns 409 with the references; `force=true` lets those messages send uncapped, so it is never used |
| Reporting webhook | Disable, then delete | It was created disabled; deleting stops nothing that was running |
| Webhook configuration | Delete after the L4 webhook actions that use it are gone | An automation's webhook action still pointing at it would fail its pre-send check, which blocks the send |
| Snippet | Delete after `GET .../snippets/{id}/usage/{continuation}` shows no use | A template referencing a deleted snippet renders the default or fails |
| Smoke profiles (`smk-<run>-`) | Smoke profiles: remove in the app (People, search smk-) | Parked by the smoke test (`marketing_blocked: true`, `unsubscribed: true`); the skill never deletes them, the user may |
| Subscription topic | Delete only if no automation or broadcast was ever assigned to it and no player preference was recorded | Player preferences are consent records; when in doubt, keep the topic |

## What is never removed
- People (profiles), under any circumstance (SKILL.md hard rule 1), except
  the synthetic smoke profiles above, which the user removes in the app. A self-excluded player's
  profile is the evidence of the exclusion and carries the confirmation and
  service mail.
- Attributes and events on profiles. The build never wrote them, so the
  rollback never touches them.
- Objects marked `existing` in the build sheet.
- The workspace's deliveries, audit log and consent history.

## Order
1. Automations created by the run: archive (or stop, then archive, if someone
   started one).
2. Reporting webhooks, then webhook configurations.
3. Frequency caps, after the usage check.
4. Lifecycle, trigger and cap segments (stage 5), dependants before the
   segments they reference.
5. Gate and suppression segments (stage 4), last among segments, because every
   other segment and every automation depends on them.
6. Snippets, after the usage check.
7. Subscription topics, only under the condition in the table.
8. Smoke profiles, in the app, at any point; nothing references them.

## Checks before each removal
- Read the object and confirm its name carries the spec ID from the build
  sheet and its ID matches the sheet.
- Read its usage (segment `usage`, cap `usage`, snippet `usage`, topic usage in
  `GET .../subscription_topics/{topic_id}`) and stop if anything outside the
  rollback list still uses it.
- After each removal, read again and record the new state in the rollback list.

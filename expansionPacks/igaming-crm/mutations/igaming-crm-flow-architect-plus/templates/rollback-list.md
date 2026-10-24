# Rollback list: [[SCOPE]]

Workspace: [[WORKSPACE_ID]] ([[sandbox|production]])
Build sheet: [[BUILD_SHEET_FILE]]

This list is for the user to carry out; the skill never removes anything.
Only build-sheet rows with Result `created` appear here. Rows marked `existing`
were in the workspace before the build and stay. People, profile attributes and
events are never removed. Message actions go with their automation and are not
listed. Order and checks: the rollback reference.

| Order | Spec ID | Type | Customer.io ID | Safe removal | Check before | Done |
|---|---|---|---|---|---|---|
| 1 | [[JRN_ID]] | automation | [[ID]] | Archive (stop first, with queued sends aborted, if someone started it) | State reads draft or stopped | [ ] |
| 2 | [[WHK_ID]] | reporting_webhook | [[ID]] | Disable, then delete | Not enabled by the backend team | [ ] |
| 3 | [[WHK_ID]] | webhook_configuration | [[ID]] | Delete | No webhook action uses it | [ ] |
| 4 | [[LIM_ID]] | frequency_cap | [[ID]] | Delete without force | Usage list is empty | [ ] |
| 5 | [[SEG_ID]] | segment | [[ID]] | Archive or delete | Usage list is empty | [ ] |
| 6 | [[SNP_ID]] | snippet | [[ID]] | Delete | Usage list is empty | [ ] |
| 7 | [[TOP_ID]] | subscription_topic | [[ID]] | Keep unless never assigned and no preference recorded | Topic usage is empty | [ ] |

Smoke profiles: remove in the app (People, search smk-). The skill parked
them and never deletes them:
[[SMK_PROFILE_IDS_OR_NONE]]

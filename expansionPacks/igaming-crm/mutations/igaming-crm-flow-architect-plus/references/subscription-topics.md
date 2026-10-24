# Subscription topics

Context: the six subscription topics, their default posture, the journeys
assigned to each, and unsubscribe mechanics. Read it for blueprint section 6,
the topic dimension of every journey, and the topic part of an audit.

## Key idea
Four marketing topics let a player opt out of one product's offers without a
global unsubscribe. Two mandatory, non-marketing topics carry RG and service
mail and cannot be unsubscribed. Once topics are enabled, every running
automation and broadcast must be assigned a subscription preference.

Topics and channels are independent: Customer.io sends only when the person is
subscribed to both the message's topic and its channel. The documentation
describes no per-topic-per-channel preference (verify before deployment), so
product x channel consent
(UK SR 5.1.12) is modelled as `consent_<product>_<channel>` attributes (data
model reference) checked in action conditions.

## Topics
| Topic (ID) | Layer | Default posture | Journeys | Unsubscribe handling |
|---|---|---|---|---|
| Casino Offers (`casino_offers`) | Marketing | Opt-in, unticked | MKT_03, MKT_04, MKT_05, MKT_06, MKT_08 casino branch, MKT_09, MKT_10 | Topic-level; other topics kept |
| Sportsbook Offers (`sportsbook_offers`) | Marketing | Opt-in, unticked | MKT_07 to sports, MKT_08 sports branch; MKT_03-06, MKT_09-10 when `preferred_product == "sportsbook"` | Topic-level |
| VIP & Loyalty (`vip_loyalty`) | Marketing | Opt-in | VIP_11 | Promotional VIP mail stops; tier-status service notices continue as transactional |
| Product Updates & Specials (`product_updates`) | Marketing | Opt-in, unticked | Broadcasts: launches, seasonal specials | Topic-level |
| Safer Gambling (`safer_gambling`) | RG, non-marketing | Mandatory | RG_12, monthly spending summary | Not unsubscribable |
| Transactional / Account (`transactional`) | Service, non-marketing | Mandatory | TXN_01, SVC_02, SYS_13, SYS_14, SYS_15 | Only by account closure |

A journey whose content depends on `preferred_product` picks the topic per
branch: casino content checks Casino Offers, sportsbook content checks
Sportsbook Offers, mixed content requires either.

## Mechanics
- Global unsubscribe sets `unsubscribed = true` and every marketing topic to
  unsubscribed; the backend receives the unsubscribed webhook and sets
  `email_marketing_consent = false`.
- One-click unsubscribe headers on every marketing email: `List-Unsubscribe`
  and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` (RFC 8058).
- The preference centre shows the four marketing toggles and a "stop all
  marketing" button; the two mandatory topics are shown locked with a short
  explanation of why they cannot be switched off.
- Every topic change sends `unsubscribe_updated` and triggers SYS_14.
- Customer.io: create topics under Settings, Subscription Topics; assign each
  journey and broadcast its topic. A topic's default (subscribed or not) is
  fixed when the topic is created and cannot be changed later.
- RG and service mail must not depend on a topic a player can leave: send it
  as transactional messages, or in automations whose topic defaults to
  subscribed and is hidden from the preference page; verify the exact
  configuration in the workspace (verify before deployment).
- Storage: `cio_subscription_preferences.topics.topic_<id>` (topic ID) and
  `cio_subscription_preferences.channels.<email|sms|push>` (channel type).
- Workspace settings: global and topic unsubscribe on; hard-bounce suppression
  on; soft-bounce suppression after 3 consecutive; automatic suppression on complaint.

## Consent posture
Marketing topics are opt-in with unticked boxes, unbundled from terms
acceptance, and withdrawable as easily as given. Consent records store
`consent_timestamp`, `consent_source` and `consent_version`. A default of
opted-in for any market (soft opt-in or pre-ticked outside the EU) is not a
design default: it is a question for counsel (legal question bank, marketing
consent category), and the deliverable states the assumption until answered.

## Footer
Every marketing email footer renders, never hardcoded: the Customer.io
unsubscribe and preference-centre link tags; operator name, address, licence
number and licensing authority from Customer.io Snippets; an 18+ notice; and
the market's safer-gambling link and helpline (the `rg_footer` snippet). The
Liquid and the snippet list are in the Liquid patterns reference.

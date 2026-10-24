# Liquid personalisation patterns

Context: Customer.io Liquid patterns for gambling CRM content, with the rules
the validator enforces (rule C10). Read it whenever a deliverable contains
Liquid: personalisation fields, zone branches, footers, spending summaries.

## Contents
- Key idea
- Rules
- Allowed tags
- Operator constants: Customer.io Snippets
- Greeting and tier
- Product preference
- Regulatory-zone footer
- Bonus eligibility content block
- First-play-only market rule
- Fail-closed backstop (marketing)
- Churn and dormant copy blocks
- VIP tier block
- Spending summary (service email)
- Marketing footer
- Webhook body values

## Key idea
Liquid shapes what an email says. It never decides whether an email is sent:
that is the gate's job (entry, action conditions, L4). Every variable has a
fallback, so a missing attribute never renders raw Liquid or an empty greeting.

## Rules
1. Every output variable carries `| default:`. The only exception is a value
   the template itself assigned with a default, or `customer.id` in a webhook
   body. The validator warns on any other output without a default (C10), and
   fails it inside a TXN, SVC, SYS or RG journey (C29).
2. Operator constants (name, address, licence, URLs, helplines) live in
   Customer.io Snippets (next section), never as hardcoded strings and never
   as an invented object. The data on a person comes from `customer.*`; the
   data on a triggering event comes from `event.*`.
3. Paired tags balance and nest correctly; `elsif`, `else` and `when` appear
   only inside their parent block.
4. Only the tags in the Customer.io tag list below. There is no tag that
   exits or suppresses a campaign; journeys stop through exit conditions and
   branches.
5. Test every template in Test Mode and Preview with a profile missing
   `first_name` and one in each regulatory zone.
6. A campaign (automation) message with a Liquid error does not send and is
   logged Failed; a transactional message sends anyway. So every variable in a
   transactional, service, system or RG template has a fallback (C29), and
   marketing templates may add the fail-closed backstop below.
7. `default` works only in the latest Liquid version; confirm the workspace
   uses it.

## Allowed tags
The Customer.io tag list. Standard: `assign`, `capture`/`endcapture`, `cycle`,
`for`/`endfor` (with `break`, `continue`), `case`/`when`/`else`/`endcase`,
`if`/`elsif`/`else`/`endif`, `unless`/`endunless`, `comment`/`endcomment`,
`raw`/`endraw`. Customer.io (single tags): `cio_link`, `cio_link_id`,
`render_liquid`, `view_in_browser_url`, `manage_subscription_preferences_url`,
`tracking_consent_url`, `unsubscribe`, `unsubscribe_url`,
`subscription_topic_name`, `countdown`, `random`, `generate_uuid`. The
validator flags any other tag name (C10). `countdown` conflicts with the
false-urgency rubric, so the validator warns on it.

## Operator constants: Customer.io Snippets
Customer.io Snippets are workspace-level pieces of reusable content, managed
in the workspace's content settings and referenced from any message as
`{{ snippets.<name> }}`. Confirm the exact reference syntax in the workspace's
snippet panel before building. Create one snippet per constant:

| Snippet | Holds | Default used in templates |
|---|---|---|
| `operator_name` | Legal entity name | "our company" |
| `operator_address` | Registered address | "the address on our website" |
| `license_authority` | Licensing authority | "the licensing authority" |
| `license_number` | Licence number | "shown on our website" |
| `rg_url` | Safer-gambling page | "https://www.begambleaware.org" |
| `limits_url` | Limits page | "your account settings" |
| `bonus_terms_url` | Bonus terms page | "the terms in your account" |
| `verify_help_url` | Account page that re-sends the verification link | "your account page" |
| `kyc_upload_url` | Document upload page | "your account verification page" |
| `br_ordinance_number` | BR licence ordinance number shown in advertising | "shown on our website" |
| `helpline_<zone>` | The zone's helpline: name and number from the `helpline` field of `references/markets.json` | the markets.json value (verify before deployment unless the row is primary for the helpline); `rg_url` only where no national helpline is known |

Snippet defaults for helplines are copied from `references/markets.json` when
the template is built (UK, DE, SE, NL, ES, IT, DK and ON at minimum); the
JSON file stays the single source.

The defaults only stop a missing snippet from rendering raw Liquid. QA_CMP_01
(QA reference) confirms the real legal values render before any template is
published; a footer showing a default value fails QA.

## Greeting and tier
```liquid
Hi {{ customer.first_name | default: "there" }},
{% if customer.vip_tier == "platinum" or customer.vip_tier == "diamond" %}
  As one of our most valued members,
{% elsif customer.vip_tier == "gold" or customer.vip_tier == "silver" %}
  As a valued member,
{% else %}
  Welcome back,
{% endif %}
```

## Product preference
```liquid
{% case customer.preferred_product %}
  {% when "sportsbook" %}
    This week's key fixtures and markets.
  {% when "casino" %}
    New slots and live tables this week.
  {% else %}
    What is new across casino and sports.
{% endcase %}
```

## Regulatory-zone footer
Helpline names and numbers come from the `helpline` field of
`references/markets.json`; each is marked "(verify before deployment)" in the
design unless its row is primary for the helpline. Keep this block in one
snippet (`rg_footer`) and include it in every marketing and RG template. The
marker stays in a Liquid comment so it is visible to the builder and never
rendered to players. Add one `when` per intake market.
```liquid
{% comment %} Helpline defaults from references/markets.json: (verify before deployment) {% endcomment %}
{% case customer.regulatory_zone %}
  {% when "UK" %}
    Please gamble responsibly. Help: {{ snippets.helpline_uk | default: "National Gambling Helpline 0808 8020 133" }}
  {% when "DE" %}
    Spielen Sie verantwortungsbewusst. Hilfe: {{ snippets.helpline_de | default: "BIÖG Telefonberatung zur Glücksspielsucht 0800 1372700" }}
  {% when "SE" %}
    Spela ansvarsfullt. Hjälp: {{ snippets.helpline_se | default: "Stödlinjen 020-81 91 00" }}
  {% when "NL" %}
    Speel verantwoord. Hulp: {{ snippets.helpline_nl | default: "OpenOverGokken 0800 2400 022" }}
  {% when "ES" %}
    Juega con responsabilidad. Ayuda: {{ snippets.helpline_es | default: "Jugadores Anónimos 900 200 225" }}
  {% when "IT" %}
    Gioca responsabilmente. Aiuto: {{ snippets.helpline_it | default: "Telefono Verde Dipendenze 800 274 274" }}
  {% when "DK" %}
    Spil ansvarligt. Hjælp: {{ snippets.helpline_dk | default: "Center for Ludomani 70 11 18 10" }}
  {% when "ON" %}
    Please play responsibly. Help: {{ snippets.helpline_on | default: "ConnexOntario 1-866-531-2600" }}
  {% else %}
    Please gamble responsibly. Help: {{ snippets.rg_url | default: "https://www.begambleaware.org" }}
{% endcase %}
```

## Bonus eligibility content block
The gate already restricts bonus emails to `SEG_CAN_RECEIVE_BONUS`; this block
is defence in depth for shared templates.
```liquid
{% if customer.bonus_eligible == true and customer.bonus_abuse_flag != true and customer.rg_risk_level == "low" %}
  Your offer: {{ event.bonus_value | default: "see account" }}.
  Wagering requirement: {{ event.wagering_requirement | default: "see terms" }}x.
  Full terms: {{ snippets.bonus_terms_url | default: "the terms in your account" }}
{% else %}
  Explore what is new in your account.
{% endif %}
```

## First-play-only market rule
SE (markets.json `first_play_only`): a bonus only at the first play occasion,
not "one welcome bonus" at any time. The journey's action condition carries
the rule; this block keeps shared templates consistent.
```liquid
{% if customer.regulatory_zone == "SE" and customer.first_play_bonus_used != true %}
  This offer applies to your first play with us.
{% elsif customer.regulatory_zone == "SE" %}
  Explore our full game library.
{% endif %}
```

## Fail-closed backstop (marketing)
A campaign message with a Liquid error does not send, so a marketing template
may stop itself when a gate-critical value is missing. Which construct reliably
raises an error in the latest Liquid is not documented (verify before
deployment); test it in the workspace. The backstop never replaces the gate,
`RG_EXIT_BLOCK` or L4, and is never used in transactional templates (they
send anyway).
```liquid
{% if customer.marketing_blocked == true or customer.self_excluded == true %}
  {% render_liquid customer.backstop_undefined_template %}
{% endif %}
```

## Churn and dormant copy blocks
```liquid
{% if customer.days_since_last_bet >= 14 and customer.days_since_last_bet < 30 %}
  Here is what is new since your last visit.
{% elsif customer.days_since_last_bet >= 30 %}
  A lot has changed. Here are the highlights.
{% endif %}
```
No references to losses, recovering money or "winning it back".

## VIP tier block
```liquid
{% case customer.vip_tier %}
  {% when "diamond" %}
    Your account manager will be in touch with your tier details.
  {% when "platinum" %}
    Your tier benefits for this month are in your account.
  {% when "gold" %}
    You are making progress toward the next tier.
  {% else %}
    Our loyalty programme rewards regular play responsibly.
{% endcase %}
```

## Spending summary (service email)
```liquid
{% assign deposits = event.deposits_total | default: 0 %}
{% assign withdrawals = event.withdrawals_total | default: 0 %}
{% assign net = deposits | minus: withdrawals %}
Your account summary for {{ event.period_label | default: "last month" }}:
Deposits: {{ deposits }} {{ customer.currency | default: "EUR" }}
Withdrawals: {{ withdrawals }} {{ customer.currency | default: "EUR" }}
Net position: {{ net }} {{ customer.currency | default: "EUR" }}
Set or review limits: {{ snippets.limits_url | default: "your account settings" }}
Safer gambling: {{ snippets.rg_url | default: "https://www.begambleaware.org" }}
```

## Marketing footer
```liquid
18+ | {{ snippets.operator_name | default: "our company" }} | {{ snippets.operator_address | default: "the address on our website" }}
Licensed by {{ snippets.license_authority | default: "the licensing authority" }}, licence {{ snippets.license_number | default: "shown on our website" }}
<a href="{% unsubscribe_url %}">Unsubscribe</a> | <a href="{% manage_subscription_preferences_url %}">Manage preferences</a>
```
`unsubscribe_url` and `manage_subscription_preferences_url` are Customer.io
tags from the allowed list, not standard Liquid. Confirm the rendered links in
Preview, and keep the one-click unsubscribe headers on.

## Webhook body values
In the L4 webhook body, use `{{ customer.id }}` for `user_id`, a literal
journey ID, and a literal `message_type`. Keep JSON samples in the design free
of Liquid so they parse; show the Liquid version next to them.

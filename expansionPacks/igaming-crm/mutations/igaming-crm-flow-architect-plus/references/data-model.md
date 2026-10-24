# Data model: player profile attributes

Context: the canonical attribute schema every deliverable uses. Read it for
blueprint section 2, for any segment or journey condition, and when mapping an
operator's own field names. The validator reads the attribute names in the
first column of these tables (rule C17) and embeds the enums (rule C19).

## Contents
- Key idea
- Attribute schema by group (identity, consent, verification, RG, risk, product
  and value, activity aggregates, frequency counters, hygiene)
- Enum values
- Sync SLAs
- identify() pattern
- Mapping operator field names

## Key idea
One Customer.io Person per player, keyed by `user_id` (never by email). All
attributes arrive through `identify()` from backend systems. Compliance-critical
attributes drive suppression and have short sync SLAs; aggregates arrive in a
daily batch. Timestamps are Unix seconds in UTC.

Used-for codes: C compliance, Seg segmentation, P personalisation, Sup
suppression, R reporting.

## Attribute schema by group

### Identity and locale
| Attribute | Type | Example | Source | Used for |
|---|---|---|---|---|
| `user_id` | string | "player_12345" | Auth service | C, Seg, R (primary id) |
| `email` | string | "player@example.com" | Registration | C, P |
| `first_name` | string | "Alex" | Registration | P |
| `country` | string ISO 3166-1 | "DE" | KYC / registration | C, Seg, P, Sup, R |
| `locale` | string BCP 47 | "de-DE" | Registration / browser | P |
| `regulatory_zone` | string | "DE" | Backend / KYC | C, Seg, Sup, R (routes overlay branches) |
| `currency` | string ISO 4217 | "EUR" | Wallet | P |
| `registered_at` | timestamp | 1751000000 | Auth service | Seg, R |
| `last_login_at` | timestamp | 1751200000 | Auth service | Seg |
| `acquisition_channel` | string | "affiliate" | Registration | Seg, R |

### Consent and channel
| Attribute | Type | Example | Source | Used for |
|---|---|---|---|---|
| `email_verified` | boolean | true | Auth service | C, Seg, Sup |
| `email_marketing_consent` | boolean | true | Consent service | C, Seg, Sup |
| `consent_timestamp` | timestamp | 1751234567 | Consent service | C, R |
| `consent_source` | string | "registration_form_v3" | Consent service | C, R |
| `consent_version` | string | "2024-01" | Consent service | C |
| `unsubscribed` | boolean | false | Customer.io / backend | C, Seg, Sup (global unsubscribe) |
| `sms_marketing_consent` | boolean | false | Consent service | C, Seg, Sup |
| `push_opt_in` | boolean | true | App | Seg |
| `last_email_engagement_at` | timestamp | 1751100000 | Customer.io webhooks | Seg (engagement, sunset) |
| `consent_betting_email` | boolean | true | Consent service | C, Seg, Sup (product x channel consent) |
| `consent_betting_sms` | boolean | false | Consent service | C, Seg, Sup |
| `consent_betting_phone` | boolean | false | Consent service | C, Seg, Sup |
| `consent_casino_email` | boolean | false | Consent service | C, Seg, Sup |
| `consent_casino_sms` | boolean | false | Consent service | C, Seg, Sup |
| `consent_casino_phone` | boolean | false | Consent service | C, Seg, Sup |
| `consent_bingo_email` | boolean | false | Consent service | C, Seg, Sup |
| `consent_bingo_sms` | boolean | false | Consent service | C, Seg, Sup |
| `consent_bingo_phone` | boolean | false | Consent service | C, Seg, Sup |

The nine `consent_<product>_<channel>` attributes are required for UK (SR
5.1.12: opt-in per product and per channel, opt-out by default) and optional
elsewhere. Customer.io topics and channels are independent preferences, so
this consent lives in attributes, not in the subscription centre.

### Verification and account
| Attribute | Type | Example | Source | Used for |
|---|---|---|---|---|
| `age_verified` | boolean | true | KYC service | C, Seg, Sup |
| `date_of_birth` | string ISO 8601 | "1990-05-15" | KYC service | C |
| `kyc_status` | enum | "approved" | KYC service | C, Seg, Sup, R |
| `kyc_verified_at` | timestamp | 1751000500 | KYC service | Seg, R |
| `account_status` | enum | "active" | Account service | C, Seg, Sup, R |
| `country_license_status` | enum | "licensed" | Compliance service | C, Seg, Sup |
| `security_flag_active` | boolean | false | Account service | Seg (pause branch) |

### Responsible gambling and protection
| Attribute | Type | Example | Source | Used for |
|---|---|---|---|---|
| `self_excluded` | boolean | false | RG service / national register | C, Seg, Sup, R |
| `self_exclusion_register` | string | "national_register" | RG service | C, R (register name) |
| `self_exclusion_source` | enum | "operator_internal" | RG service | C, R |
| `self_exclusion_register_match` | boolean | false | Register integration | C, Seg, Sup |
| `marketing_blocked` | boolean | false | CRM operations / compliance | C, Seg, Sup (kill switch; exits every marketing automation through `RG_EXIT_BLOCK`) |
| `timeout_active` | boolean | false | RG service | C, Seg, Sup |
| `excluded_until` | timestamp | 1760000000 | RG service | C, Sup |
| `rg_risk_level` | enum | "low" | RG algorithm | C, Seg, Sup, R |
| `limit_active` | boolean | true | Account service | Seg (no limit-increase messaging) |
| `deposit_limit_active` | boolean | true | Account service | Seg |
| `lugas_limit_eur` | float | 1000.0 | Register integration (DE) | C, R (never used to prompt a raise) |
| `lugas_limit_set_at` | timestamp | 1751000000 | Register integration (DE) | C, R |
| `nl_affordability_check_status` | enum | "not_required" | Compliance service (NL) | C, Seg, Sup |
| `nl_staff_contact_done` | boolean | false | Compliance service (NL) | C |
| `betguard_checked_at` | timestamp | 1751000000 | Register integration (ON) | C, Sup |

### Risk and bonus eligibility
| Attribute | Type | Example | Source | Used for |
|---|---|---|---|---|
| `aml_status` | enum | "clear" | Compliance service | C, Seg, Sup |
| `fraud_flag` | boolean | false | Fraud service | C, Seg, Sup |
| `bonus_eligible` | boolean | true | Bonus service | Seg, Sup |
| `bonus_abuse_flag` | boolean | false | Bonus service | C, Seg, Sup |
| `first_play_bonus_used` | boolean | false | Bonus service | C, Sup (first-play-only markets such as SE: the bonus is offered only at the first play occasion) |

### Product and value
| Attribute | Type | Example | Source | Used for |
|---|---|---|---|---|
| `preferred_product` | enum | "casino" | Behaviour model | Seg, P, R |
| `preferred_sport` | string | "football" | Sportsbook | P |
| `preferred_casino_category` | string | "live_casino" | Game engine | P |
| `vip_tier` | enum | "gold" | Loyalty service | Seg, P, R |
| `vip_status` | enum | "vip" | Loyalty service | Seg, P, R |
| `vip_progress_pct` | integer | 64 | Loyalty service | P |
| `first_deposit_at` | timestamp | 1740000000 | Payment service | Seg, P, R |
| `last_deposit_at` | timestamp | 1751000000 | Payment service | Seg, R |
| `lifetime_deposits` | integer (count) | 12 | Payment service | Seg, P, R |
| `lifetime_withdrawals` | integer (count) | 3 | Payment service | R |
| `lifetime_ggr` | float | 450.75 | Finance | Seg, R |
| `real_money_balance` | float | 18.40 | Wallet | Seg (balance notice on dormant accounts) |
| `active_bonus_id` | string | "RELOAD50" | Bonus service | P |
| `wagering_progress_pct` | integer | 40 | Bonus service | P |
| `churn_risk_score` | float 0-1 | 0.32 | ML service | Seg, R |

### Activity aggregates (daily batch unless noted)
| Attribute | Type | Example | Source | Used for |
|---|---|---|---|---|
| `last_play_at` | timestamp | 1751100000 | Game engine (real time) | Seg, R |
| `last_bet_at` | timestamp | 1751100000 | Game engine (real time) | Seg, R |
| `days_since_last_play` | integer | 3 | Session analytics | Seg, R |
| `days_since_last_bet` | integer | 3 | Session analytics | Seg, R |
| `days_since_last_deposit` | integer | 9 | Payment analytics | Seg |
| `sessions_last_7d` | integer | 4 | Session analytics | Seg (RG monitoring) |
| `sessions_last_30d` | integer | 8 | Session analytics | Seg, R |
| `session_duration_avg_mins` | integer | 45 | Session analytics | Seg (RG monitoring) |
| `deposits_last_7d` | integer | 1 | Payment analytics | Seg (RG monitoring) |
| `deposits_last_30d` | integer | 4 | Payment analytics | Seg, R |
| `ggr_last_7d` | float | 30.00 | Finance | Seg (RG loss velocity) |
| `ggr_last_30d` | float | 125.50 | Finance | Seg, R |
| `ggr_last_90d` | float | 310.00 | Finance | Seg (VIP qualification) |
| `casino_bets_last_90d` | integer | 45 | Game engine | Seg, R |
| `sports_bets_last_90d` | integer | 0 | Sportsbook | Seg, R |

`last_bet_at` and `days_since_last_bet` count any real-money wager: casino
rounds and sportsbook bets. Event-wise, a casino wager arrives as
`game_played` and a sportsbook wager as `bet_placed`, so journeys that exit on
"any wager" list both events.

### Frequency counters and caps (backend counter service)
| Attribute | Type | Example | Source | Used for |
|---|---|---|---|---|
| `marketing_emails_sent_today` | integer | 0 | Counter service | C, Sup |
| `marketing_emails_sent_last_7d` | integer | 2 | Counter service | C, Seg, Sup, R |
| `bonus_emails_sent_last_7d` | integer | 1 | Counter service | Sup |
| `cross_sell_emails_sent_last_7d` | integer | 0 | Counter service | Sup |
| `last_marketing_email_sent_at` | timestamp | 1751050000 | Counter service | Sup (cooldown) |
| `frequency_cap_reached` | boolean | false | Counter service (most restrictive cap) | Sup |
| `bonus_cap_reached` | boolean | false | Counter service | Sup |
| `cross_sell_cap_reached` | boolean | false | Counter service | Sup |

### Hygiene
| Attribute | Type | Example | Source | Used for |
|---|---|---|---|---|
| `sunset_suppressed` | boolean | false | Set by JRN_SYS_15 | Sup (list hygiene) |

## Enum values
- `kyc_status`: not_started, in_progress, approved, provisional_allowed, rejected, expired
- `account_status`: active, suspended, restricted, closed, pending_verification
- `country_license_status`: licensed, unlicensed, pending, restricted
- `rg_risk_level`: low, medium, high, severe
- `aml_status`: clear, monitoring, blocked, frozen, restricted
- `preferred_product`: casino, sportsbook, poker, mixed, unknown
- `vip_tier`: none, bronze, silver, gold, platinum, diamond
- `vip_status`: standard, vip, host_managed
- `self_exclusion_source`: operator_internal, national_register, support_agent, multi_operator_scheme
- `nl_affordability_check_status`: not_required, pending, passed, failed

Operator constants such as the Brazilian ordinance number are not player
attributes: they live in Customer.io Snippets (`br_ordinance_number`, Liquid
patterns reference).

Values outside these lists ("verified", "pending", "none" for RG, "resolved")
are errors (validator rule C19). An operator with different tier names maps
them onto `vip_tier` and states the mapping.

## Sync SLAs
| SLA | Attributes |
|---|---|
| Real time | consent fields (including every `consent_<product>_<channel>`), `marketing_blocked`, registration fields, `last_play_at`, `last_bet_at`, deposit events, and the deposit-count fields `lifetime_deposits`, `first_deposit_at`, `last_deposit_at` (the payment service sends `identify()` with them before the matching `track("deposit_successful")`) |
| 5 minutes | `self_excluded`, `self_exclusion_source`, `self_exclusion_register_match`, `timeout_active`, `excluded_until`, `account_status`, `kyc_status`, `age_verified`, `lugas_limit_eur`, `nl_affordability_check_status`, `nl_staff_contact_done`, `betguard_checked_at` |
| 15 minutes | `rg_risk_level`, `aml_status`, `fraud_flag`, `vip_tier`, `vip_status` |
| 1 hour | frequency counters and the three `*_cap_reached` flags |
| Daily batch 02:00 UTC | GGR, windowed deposit and session aggregates (`deposits_last_7d`, `deposits_last_30d`, `sessions_*`), `churn_risk_score`, `days_since_*` |

## identify() pattern
```json
{
  "type": "identify",
  "id": "player_12345",
  "attributes": {
    "email_marketing_consent": true,
    "account_status": "active",
    "kyc_status": "approved",
    "rg_risk_level": "low",
    "self_excluded": false,
    "days_since_last_bet": 3,
    "ggr_last_30d": 125.50,
    "marketing_emails_sent_last_7d": 2
  }
}
```

## Mapping operator field names
When the operator already uses other names (for example `customer_id`,
`global_unsubscribe`, `deposit_count`), keep the canonical name in the design
and add a mapping table (operator field, canonical attribute, transform). Do
not mix both names inside segment logic.

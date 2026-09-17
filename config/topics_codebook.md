# ReleaseRadar Topic Codebook — DRAFT (v0)

> **Status:** draft, seeded from domain knowledge of UPI apps.
> This will be revised in Phase 4 after running BERTopic on a sample of real
> reviews — topics may be split, merged, renamed, or added based on what
> actually appears in the data. Do not start hand-labeling until this file
> is marked v1 (post-BERTopic review).

Reviews are **multi-label**: a single review can carry more than one topic
tag (e.g. a review can be both `payment_failure` and `customer_support`).

## Topics

| Key | Definition | Include | Exclude | Example |
|---|---|---|---|---|
| `payment_failure` | Transaction failed, stuck/pending, debited but not received at the other end | "money deducted but not received", "transaction failed" | Refund-specific complaints (→ `refund_delay`) | "money deducted but not received by merchant" |
| `refund_delay` | Refund/reversal for a failed transaction not received or slow | "refund not credited", "reversal pending" | The original failure itself (tag both if mentioned) | "refund not come after 7 days" |
| `login_otp_kyc` | Problems logging in, receiving OTP, setting PIN, or completing KYC/re-verification | "OTP not coming", "KYC failed" | Account being blocked/frozen (→ `account_blocked`) | "OTP not received for 20 minutes" |
| `account_blocked` | Account frozen, suspended, or restricted by the app/bank | "my account is blocked", "suspended without reason" | Login friction unrelated to a block (→ `login_otp_kyc`) | "account blocked for no reason" |
| `bank_linking` | Can't add/link a bank account or UPI ID, bank server errors during linking | "bank server not found", "can't add bank account" | General payment failures after linking is done | "unable to link SBI account" |
| `app_performance` | App is slow, crashes, freezes, or won't open | "app hangs", "crashes on open" | Slowness specifically during a payment (tag both if ambiguous) | "app freezes every time I open it" |
| `ui_ux` | Confusing design, hard to find a feature, disliked redesign | "new update UI is confusing", "can't find old feature" | Ads/notifications (→ `ads_spam`) | "new update ruined the layout" |
| `customer_support` | Can't reach support, bot-only support, unresolved tickets | "no customer care number", "chatbot useless" | — | "no way to talk to a human" |
| `fraud_security` | Scam, unauthorized debit, phishing, security concerns | "unauthorized transaction", "scam call" | Legitimate failed payment (→ `payment_failure`) | "money stolen via fake QR code" |
| `rewards_cashback` | Cashback, scratch cards, reward point complaints or praise | "no cashback anymore", "scratch card is fake" | Platform fees (→ `fees_charges`) | "cashback never credited" |
| `fees_charges` | Platform fee, convenience fee, hidden/unexpected charges | "charging fee on recharge", "hidden charges" | Rewards/cashback (→ `rewards_cashback`) | "now charging ₹5 per bill payment" |
| `ads_spam` | Too many ads, promotional notifications, spam | "too many notifications", "ads everywhere" | — | "notification every 10 minutes" |
| `bills_recharge` | Problems with bill payment / mobile recharge specifically | "recharge failed", "bill payment not going through" | General payment failure unrelated to bills/recharge | "recharge done but not activated" |
| `general_praise` | Positive review with no specific actionable topic | "very good app", "excellent" | Praise that names a specific feature (tag that feature too) | "best app ever" |
| `uninformative` | Too short/vague to classify into any topic above | "bad", "ok", "nice" | — | "worst" |

## Flags (separate from topics — every review gets these too)

| Flag | Definition | Values |
|---|---|---|
| `churn_intent` | Reviewer explicitly states they are uninstalling, leaving, or switching away | `true` / `false` |
| `competitor_mentioned` | Reviewer names a specific competitor app (see `aliases.yaml`) | app key or `null` |

## Labeling rules
1. Apply **every** topic that clearly applies — do not force a single label.
2. When in doubt between two adjacent topics (e.g. `payment_failure` vs.
   `refund_delay`), apply **both** if the review mentions both stages.
3. `uninformative` is used **only** when no other topic can be determined —
   it is not a catch-all for negative reviews in general.
4. `churn_intent = true` requires an explicit statement of leaving
   ("uninstalling", "switching to X", "done with this app") — a low rating
   alone is not churn intent.
5. Reviews may be in Hinglish (Hindi in Latin script) — label by meaning,
   not by English keyword matching alone.

## Revision log
- v0 (2026-09-17): initial draft, pre-data.

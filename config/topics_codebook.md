# ReleaseRadar Topic Codebook — v1

> **Status:** validated against real data. BERTopic was run on 25,000
> reviews with 5+ words (Phase 4.1, 2026-09-18) to check the v0 draft
> against actual review content before hand-labeling began. See the
> revision log at the bottom for what changed and why.

Reviews are **multi-label**: a single review can carry more than one
topic tag (e.g. a review can be both `payment_failure` and
`customer_support`).

**A major discovery-stage finding:** the single largest cluster BERTopic
found (n=3,115 of 25,000 sampled, ~12.5% — by far the biggest cluster)
was almost entirely **Hindi/Hinglish text** (e.g. "mere mobile par nahi
chal raha hai login nahi ho raha hai", "upi Nhi chal raha 😤"). This is
stronger evidence than the Phase 3 EDA's rough keyword-marker proxy
suggested — Hinglish is not a minor edge case, it's central to the
corpus. The classifier (Phase 4.4) must handle it as a first-class case,
not an afterthought.

## Topics

| Key | Definition | Include | Exclude | Example (from real data) |
|---|---|---|---|---|
| `payment_failure` | Transaction failed, stuck/pending, debited but not received at the other end | "money deducted but not received", "transaction failed", UPI/login not working (Hindi: "chal nahi raha", "nahi ho raha") | Refund-specific complaints (→ `refund_delay`) | "lot of transaction issue now a days" |
| `refund_delay` | Refund/reversal for a failed **payment transaction** not received or slow | "refund not credited", "reversal pending" | Travel/booking refunds (→ `travel_booking`); the original failure itself (tag both if mentioned) | "if the payment failed its your mistake..so why take my coupon?" |
| `login_otp_kyc` | Problems logging in, receiving OTP, setting/entering PIN, or completing KYC/re-verification | "OTP not coming", "KYC failed", PIN keypad/UI entry issues, PIN digit-count mismatches | Account being blocked/frozen (→ `account_blocked`) | "my upi pin is 6 digits but gpay is showing only 4 digit option to enter" |
| `account_blocked` | Account frozen, suspended, or restricted by the app/bank; punitive fees tied to account status | "my account is blocked", "suspended without reason", inactivity-fee threats | Login friction unrelated to a block (→ `login_otp_kyc`) | "without any information just blocked my phonepe account without any reason" |
| `bank_linking` | Can't add/link a bank account or UPI ID, bank server errors during linking | "bank server not found", "can't add bank account", "account is invalid please remove and add again" | General payment failures after linking is done | "oops something went wrong on loop when trying to add a bank account" |
| `app_performance` | App is slow, crashes, freezes, won't open, or a device/QR-scanner malfunction | "app hangs", "crashes on open", "device environment not correct", QR scanner not working | Slowness specifically during a payment (tag both if ambiguous) | "app not working since a week, it automatically close" |
| `ui_ux` | Confusing design, hard to find a feature, disliked redesign | "new update UI is confusing", "can't find old feature" | Ads/notifications (→ `ads_spam`); PIN-entry-specific UI (→ `login_otp_kyc`) | (lower frequency in discovery sample; kept from domain knowledge) |
| `customer_support` | Can't reach support, bot-only support, unresolved tickets | "no customer care number", "chatbot useless" | — | "couldn't contact the customer supporter there are ignoring" |
| `fraud_security` | Scam, unauthorized debit, phishing, security concerns | "unauthorized transaction", "scam call" | Legitimate failed payment (→ `payment_failure`) | (lower frequency in discovery sample; kept from domain knowledge as a high-severity category worth tracking even if rare) |
| `rewards_cashback` | Cashback, scratch cards, reward point complaints or praise | "no cashback anymore", "scratch card is fake", "never blessed me with a good cashback" | Platform fees (→ `fees_charges`) | "using ts for almost 4yrs and they never blessed me with a good cashback" |
| `fees_charges` | Platform fee, convenience fee, hidden/unexpected charges, wallet-inactivity fees | "charging fee on recharge", "hidden charges", "platform charges are too high" | Rewards/cashback (→ `rewards_cashback`) | "platform charges are too high" |
| `ads_spam` | Too many ads, promotional notifications, spam | "too many notifications", "ads everywhere" | — | (lower frequency in discovery sample; kept from domain knowledge) |
| `bills_recharge` | Problems with bill payment / mobile recharge specifically | "recharge failed", "bill payment not going through" | General payment failure unrelated to bills/recharge | "mobile recharge option is not working, app is getting closed repeatedly" |
| `autopay_mandates` | **NEW (v1):** UPI Autopay / recurring-mandate setup, cancellation, or unwanted-charge issues | "autopay option is not available", "already cancelled autopay still trying to charge me", can't delete/cancel a mandate | A one-time payment failure unrelated to a standing mandate (→ `payment_failure`) | "I already cancelled Autopay still gpay is trying to charge me" |
| `investments_gold` | **NEW (v1):** digital gold/silver or other in-app investment feature complaints or requests | "worst experience in selling digital silver", live P&L tracking requests, gold/silver price complaints | — | "worst experience in selling digital silver" |
| `travel_booking` | **NEW (v1):** bus/flight/train ticket booking and refund issues (a distinct product vertical from UPI payments) | "bus operator cancel the journey refund issue", airline/operator refund routing delays via the app | UPI transaction refunds unrelated to travel (→ `refund_delay`) | "they are not refunding my multiple booking cancellations" |
| `general_praise` | Positive with no specific actionable topic | "very good app", "excellent" | Praise that names a specific feature (tag that feature too) | "best app ever" |
| `uninformative` | Too short/vague to classify into any topic above, OR generic negative venting with no specific actionable complaint | "bad", "ok", "nice", "worst app in the world" | A rant that also names a specific issue (tag both — e.g. "WORST APP...TRANSACTION FAIL" gets `uninformative` AND `payment_failure`) | "worst app in the world" |

## Flags (separate from topics — every review gets these too)

| Flag | Definition | Values |
|---|---|---|
| `churn_intent` | Reviewer explicitly states they are uninstalling, leaving, or switching away | `true` / `false` |
| `competitor_mentioned` | Reviewer names a specific competitor app (see `aliases.yaml`) | app key or `null` |

## Labeling rules
1. Apply **every** topic that clearly applies — do not force a single label.
2. When in doubt between two adjacent topics (e.g. `payment_failure` vs.
   `refund_delay`), apply **both** if the review mentions both stages.
3. `uninformative` is used for short/vague reviews **or** generic
   negative venting — but if the same review also names a specific
   issue, tag both `uninformative` and the specific topic. It is not a
   catch-all that excludes other tags.
4. `churn_intent = true` requires an explicit statement of leaving
   ("uninstalling", "switching to X", "done with this app") — a low
   rating alone is not churn intent.
5. Reviews may be in Hinglish (Hindi in Latin script) or Hindi in
   Devanagari script — label by meaning, not by English keyword
   matching alone. This is common, not rare (see the discovery finding
   above), and requires active attention while labeling, not a
   best-effort guess.

## Revision log
- **v0 (2026-09-17):** initial draft, pre-data, based on domain
  knowledge of UPI apps.
- **v1 (2026-09-18):** validated against BERTopic run on 25,000 reviews
  with 5+ words (26.3% fell into the unclustered/outlier bucket, typical
  for short noisy review text). Changes:
  - **Added 3 new topics** found in real data that weren't anticipated
    in v0: `autopay_mandates`, `investments_gold`, `travel_booking` —
    all reflect product features (recurring payments, in-app
    investing, travel booking) that these "UPI apps" have actually
    expanded into, beyond pure payments.
  - **Confirmed Hinglish/Hindi is central**, not an edge case — the
    single largest discovered cluster (12.5% of the sample) was
    Hindi/Hinglish text, a stronger finding than Phase 3's rough
    keyword-marker EDA proxy suggested.
  - **Confirmed `general_praise` as a single bucket is correct** despite
    BERTopic splitting positive reviews into ~15 separate small
    clusters — inspection showed this fragmentation is a phrasing
    artifact ("very good app" vs. "nice" vs. "best app ever" cluster
    separately), not evidence of meaningfully different sub-topics.
  - **Folded in specific inclusion examples** for `app_performance`
    (QR scanner issues), `login_otp_kyc` (PIN-entry UI problems), and
    `fees_charges` (wallet-inactivity fees) based on real clusters that
    would otherwise have been ambiguous to a labeler.
  - `fraud_security` and `ads_spam` were **not prominently surfaced** in
    the top ~48 clusters reviewed — kept in the codebook from domain
    knowledge (worth tracking even if rare, especially `fraud_security`
    for Phase 8's issue-cost ranking, where severity matters more than
    raw frequency), but flagged here as possibly lower-prevalence than
    originally assumed. Will confirm actual prevalence once labeling is
    complete.

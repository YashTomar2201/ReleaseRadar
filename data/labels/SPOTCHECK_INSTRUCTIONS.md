# Blind Spot-Check Instructions

**Purpose:** you're independently labeling 120 reviews (already sampled from
the classifier's held-out test set) so we can compute a real human-vs-AI
agreement score (Cohen's kappa) — this is what makes the classifier's
accuracy claim defensible in an interview, instead of "an AI checked its
own work."

**File to fill in:** `spotcheck_blind.csv` (open in Excel / Google Sheets)

**Do NOT open** `spotcheck_answer_key.csv` until you're done — it has
the AI's labels for the same rows, and looking at it first defeats the
whole point of a blind check.

## How to fill it in

Each row is one review. For each of the 18 topic columns, enter:
- `1` if that topic applies to the review
- `0` (or leave blank) if it doesn't
- A review can have **multiple topics** — that's expected, tag every
  topic that clearly applies.

For `churn_intent`: `1` only if the reviewer explicitly says they're
uninstalling, switching to a named/unnamed competitor, or done with the
app. A low rating alone is NOT churn intent.

For `competitor_mentioned`: type the competitor's name if one is named
(phonepe / gpay / paytm / bhim / cred / amazonpay / navi / supermoney),
otherwise leave blank.

**Reference the codebook** at `config/topics_codebook.md` — it has the
full definition, include/exclude rules, and an example for every topic.
Keep it open in another tab while labeling.

## Topics (quick reference — full definitions in the codebook)

| Topic | One-line meaning |
|---|---|
| `payment_failure` | Transaction failed/stuck/pending |
| `refund_delay` | Refund for a failed payment not received |
| `login_otp_kyc` | Login, OTP, PIN entry, KYC problems |
| `account_blocked` | Account frozen/suspended/restricted |
| `bank_linking` | Can't add/link a bank account |
| `app_performance` | Crashes, freezes, won't open, slow |
| `ui_ux` | Confusing design, missing feature request |
| `customer_support` | Can't reach support, unresolved tickets |
| `fraud_security` | Scam, unauthorized debit, security concern |
| `rewards_cashback` | Cashback/rewards complaints or praise |
| `fees_charges` | Platform fees, hidden charges |
| `ads_spam` | Too many ads/notifications |
| `bills_recharge` | Bill payment / mobile recharge specifically |
| `autopay_mandates` | UPI Autopay setup/cancellation/unwanted charges |
| `investments_gold` | Digital gold/silver/mutual fund features |
| `travel_booking` | Bus/flight/train ticket booking & refunds |
| `general_praise` | Positive, no specific actionable topic |
| `uninformative` | Too short/vague, or generic venting with no specific issue |

## When you're done

Save `spotcheck_blind.csv` and let me know — I'll run
`src/classify/score_spotcheck.py` to compute per-topic agreement
(Cohen's kappa) between your labels and the AI's, which becomes the
real validation number in the methodology doc and README.

**Time estimate:** roughly 1.5-2.5 hours for 120 short reviews.

"""Build the blind human spot-check packet (hybrid labeling validation,
per decision_log.md 2026-09-18). Samples 120 reviews from the TEST split
specifically (not dev) -- that's the split final accuracy numbers get
reported against, so a human check on exactly those rows is the most
decision-relevant validation.

Produces:
  data/labels/spotcheck_blind.csv   -- for the user to fill in (NO AI
                                        labels visible; topic columns
                                        are empty 0/1 fields)
  data/labels/spotcheck_answer_key.csv  -- AI labels for the same rows,
                                        kept separate so filling in the
                                        blind sheet stays truly blind
"""
import pandas as pd

TOPICS = [
    "payment_failure", "refund_delay", "login_otp_kyc", "account_blocked",
    "bank_linking", "app_performance", "ui_ux", "customer_support",
    "fraud_security", "rewards_cashback", "fees_charges", "ads_spam",
    "bills_recharge", "autopay_mandates", "investments_gold",
    "travel_booking", "general_praise", "uninformative",
]

N_SPOTCHECK = 120
SEED = 7

gold = pd.read_csv(r"D:\projects\non-tech\data\labels\gold_labels.csv")
test_rows = gold[gold["split"] == "test"].copy()

# Stratified by app so the spot-check isn't accidentally skewed to one app
parts = []
for app, g in test_rows.groupby("app_key"):
    n = round(N_SPOTCHECK * len(g) / len(test_rows))
    parts.append(g.sample(n=n, random_state=SEED))
spot = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)  # shuffle order

# --- Answer key (AI labels), kept separate ---
answer_key = spot[["review_id", "topics", "churn_intent", "competitor_mentioned"]].copy()
answer_key.to_csv(r"D:\projects\non-tech\data\labels\spotcheck_answer_key.csv", index=False, encoding="utf-8")

# --- Blind packet for the user ---
blind = spot[["review_id", "app_key", "rating", "review_text"]].copy()
for t in TOPICS:
    blind[t] = ""  # fill with 0/1
blind["churn_intent"] = ""       # fill with 0/1
blind["competitor_mentioned"] = ""  # fill with app name or leave blank
blind.to_csv(r"D:\projects\non-tech\data\labels\spotcheck_blind.csv", index=False, encoding="utf-8")

print(f"Spot-check packet built: {len(blind)} reviews")
print(blind["app_key"].value_counts())
print("\nFiles:")
print("  data/labels/spotcheck_blind.csv       <- fill this in")
print("  data/labels/spotcheck_answer_key.csv  <- do not open until done labeling")

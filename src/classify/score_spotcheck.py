"""Score the completed blind spot-check against the AI answer key.
Run this AFTER spotcheck_blind.csv has been filled in by hand.

Computes, per topic: Cohen's kappa, precision/recall/F1 (treating the
human as ground truth), and overall multi-label agreement -- this is
the real, defensible validation number for the classifier, since it's
an independent human check rather than an AI checking itself.
"""
import pandas as pd
from sklearn.metrics import cohen_kappa_score, precision_recall_fscore_support

TOPICS = [
    "payment_failure", "refund_delay", "login_otp_kyc", "account_blocked",
    "bank_linking", "app_performance", "ui_ux", "customer_support",
    "fraud_security", "rewards_cashback", "fees_charges", "ads_spam",
    "bills_recharge", "autopay_mandates", "investments_gold",
    "travel_booking", "general_praise", "uninformative",
]

blind = pd.read_csv(r"D:\projects\non-tech\data\labels\spotcheck_blind.csv")
answer_key = pd.read_csv(r"D:\projects\non-tech\data\labels\spotcheck_answer_key.csv")

merged = blind.merge(answer_key, on="review_id", suffixes=("_human", "_ai"))
assert len(merged) == len(blind), "Row count mismatch after merge -- check review_id join"

ai_topic_sets = merged["topics"].apply(lambda s: set(str(s).split(";")) if pd.notna(s) else set())

results = []
for topic in TOPICS:
    human_col = merged[topic].fillna(0).astype(int).clip(0, 1)
    ai_col = ai_topic_sets.apply(lambda s: int(topic in s))

    if human_col.sum() == 0 and ai_col.sum() == 0:
        results.append({"topic": topic, "kappa": None, "precision": None,
                         "recall": None, "f1": None, "support_human": 0, "support_ai": 0,
                         "note": "no positive examples in either -- not scoreable"})
        continue

    kappa = cohen_kappa_score(human_col, ai_col)
    p, r, f1, _ = precision_recall_fscore_support(
        human_col, ai_col, average="binary", zero_division=0
    )
    results.append({
        "topic": topic, "kappa": round(kappa, 3), "precision": round(p, 3),
        "recall": round(r, 3), "f1": round(f1, 3),
        "support_human": int(human_col.sum()), "support_ai": int(ai_col.sum()),
        "note": "" if human_col.sum() >= 5 else "LOW SUPPORT -- interpret cautiously",
    })

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))

scoreable = results_df.dropna(subset=["kappa"])
print(f"\nMacro-average kappa across {len(scoreable)} scoreable topics: {scoreable['kappa'].mean():.3f}")
print(f"Macro-average F1: {scoreable['f1'].mean():.3f}")

# churn_intent
h_churn = merged["churn_intent_human"].fillna(0).astype(int).clip(0, 1)
a_churn = merged["churn_intent_ai"].astype(int)
print(f"\nchurn_intent kappa: {cohen_kappa_score(h_churn, a_churn):.3f} "
      f"(human positives: {h_churn.sum()}, AI positives: {a_churn.sum()})")

results_df.to_csv(r"D:\projects\non-tech\data\labels\spotcheck_results.csv", index=False)
print("\nSaved to data/labels/spotcheck_results.csv")

"""Phase 4.4/4.5: evaluate the trained classifier on the untouched
450-review test split. Reports per-topic precision/recall/F1, flagging
low-support topics explicitly rather than reporting a misleadingly
precise number for a topic with 0-3 test examples.
"""
import pickle

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, f1_score

TOPICS = [
    "payment_failure", "refund_delay", "login_otp_kyc", "account_blocked",
    "bank_linking", "app_performance", "ui_ux", "customer_support",
    "fraud_security", "rewards_cashback", "fees_charges", "ads_spam",
    "bills_recharge", "autopay_mandates", "investments_gold",
    "travel_booking", "general_praise", "uninformative",
]

MIN_SUPPORT_FOR_RELIABLE_SCORE = 5


def main():
    gold = pd.read_csv(r"D:\projects\non-tech\data\labels\gold_labels.csv")
    test = gold[gold["split"] == "test"].copy()
    test["topic_list"] = test["topics"].apply(lambda s: str(s).split(";") if pd.notna(s) else [])

    with open(r"D:\projects\non-tech\data\interim\topic_classifier.pkl", "rb") as f:
        bundle = pickle.load(f)
    clf, mlb, model_name = bundle["clf"], bundle["mlb"], bundle["model_name"]

    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer(model_name)
    X_test = encoder.encode(test["review_text"].tolist(), show_progress_bar=True, batch_size=64)

    Y_test = mlb.transform(test["topic_list"])
    Y_pred = clf.predict(X_test)  # flat 0.5 threshold, per train_classifier.py's documented simplification

    print(f"Evaluating on {len(test)} held-out test reviews (never used in training)\n")

    rows = []
    for i, topic in enumerate(TOPICS):
        support_test = int(Y_test[:, i].sum())
        support_train_note = ""
        report = classification_report(
            Y_test[:, i], Y_pred[:, i], output_dict=True, zero_division=0
        )
        p, r, f1 = report["1"]["precision"], report["1"]["recall"], report["1"]["f1-score"]
        flag = "" if support_test >= MIN_SUPPORT_FOR_RELIABLE_SCORE else "LOW SUPPORT -- interpret cautiously"
        rows.append({
            "topic": topic, "support_test": support_test,
            "precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3),
            "note": flag,
        })

    results = pd.DataFrame(rows).sort_values("support_test", ascending=False)
    print(results.to_string(index=False))

    reliable = results[results["support_test"] >= MIN_SUPPORT_FOR_RELIABLE_SCORE]
    print(f"\n=== Macro-F1 across {len(reliable)} topics with >= {MIN_SUPPORT_FOR_RELIABLE_SCORE} test examples: "
          f"{reliable['f1'].mean():.3f} ===")
    print(f"=== Macro-F1 across ALL {len(results)} topics (including low-support): {results['f1'].mean():.3f} ===")

    micro_f1 = f1_score(Y_test, Y_pred, average="micro", zero_division=0)
    print(f"=== Micro-F1 (all topics, all test rows): {micro_f1:.3f} ===")

    results.to_csv(r"D:\projects\non-tech\data\labels\classifier_eval_results.csv", index=False)
    print("\nSaved to data/labels/classifier_eval_results.csv")


if __name__ == "__main__":
    main()

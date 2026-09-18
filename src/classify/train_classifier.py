"""Phase 4.4, Step B: train a lightweight multi-label classifier
(multilingual sentence embeddings + one-vs-rest logistic regression) on
the dev split of the gold label set, to be applied to the full 291K-review
corpus in Step C.

Honest limitation (see decision_log.md 2026-09-18): training data is
only the 150-review dev split -- there was no budget/API access to run
a separate large-scale LLM bulk-labeling pass (the roadmap's original
Step A) as an independent process, since the labeler here is Claude
directly rather than a callable API. Per-topic threshold tuning is
skipped (uses a flat 0.5 threshold) rather than searched on the same 150
rows used for training -- with this little data, a per-topic threshold
search would just be overfitting noise, not a real calibration.
"""
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

TOPICS = [
    "payment_failure", "refund_delay", "login_otp_kyc", "account_blocked",
    "bank_linking", "app_performance", "ui_ux", "customer_support",
    "fraud_security", "rewards_cashback", "fees_charges", "ads_spam",
    "bills_recharge", "autopay_mandates", "investments_gold",
    "travel_booking", "general_praise", "uninformative",
]

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # same one used for BERTopic; copes with Hinglish


def main():
    gold = pd.read_csv(r"D:\projects\non-tech\data\labels\gold_labels.csv")
    dev = gold[gold["split"] == "dev"].copy()
    n_test = (gold["split"] == "test").sum()

    # Rare-topic training boost (decision_log.md 2026-09-18): keyword-
    # guided additional training examples for topics that had 0-3
    # examples in the random 150-row dev split. Built from reviews
    # explicitly excluded from gold_sample.csv, so it cannot overlap
    # with either the dev or (crucially) the test split.
    boost_path = Path(r"D:\projects\non-tech\data\labels\rare_topic_boost_labels.csv")
    if boost_path.exists():
        boost = pd.read_csv(boost_path)
        boost = boost[["review_id", "app_key", "rating", "review_text", "text_length",
                        "topics", "churn_intent", "competitor_mentioned"]].copy()
        boost["split"] = "dev_boost"
        train = pd.concat([dev, boost], ignore_index=True)
        print(f"Training on {len(dev)} dev-split + {len(boost)} rare-topic-boost reviews "
              f"= {len(train)} total (test split of {n_test} left untouched)")
    else:
        train = dev
        print(f"Training on {len(train)} dev-split reviews only (no boost file found) "
              f"(test split of {n_test} left untouched)")

    train["topic_list"] = train["topics"].apply(lambda s: str(s).split(";") if pd.notna(s) else [])

    print(f"Loading embedding model: {MODEL_NAME}")
    encoder = SentenceTransformer(MODEL_NAME)

    X_train = encoder.encode(train["review_text"].tolist(), show_progress_bar=True, batch_size=64)

    mlb = MultiLabelBinarizer(classes=TOPICS)
    Y_train = mlb.fit_transform(train["topic_list"])

    print("\nPer-topic training support (dev split):")
    for i, t in enumerate(TOPICS):
        print(f"  {t:20s} {Y_train[:, i].sum():3d}")

    clf = OneVsRestClassifier(LogisticRegression(max_iter=2000, class_weight="balanced"))
    clf.fit(X_train, Y_train)

    with open(r"D:\projects\non-tech\data\interim\topic_classifier.pkl", "wb") as f:
        pickle.dump({"clf": clf, "mlb": mlb, "model_name": MODEL_NAME}, f)

    print("\nSaved classifier to data/interim/topic_classifier.pkl")


if __name__ == "__main__":
    main()

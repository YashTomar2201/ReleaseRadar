"""Phase 4.4, Step C: apply the trained classifier to all 291K reviews
in the corpus, and load results back into DuckDB as raw.review_topics
(long format: one row per review-topic pair) and raw.review_flags
(churn_intent -- competitor_mentioned is handled separately in Phase 7,
since it needs the fuller alias-matching + relation classification, not
just this topic classifier).
"""
import pickle

import duckdb
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

TOPICS = [
    "payment_failure", "refund_delay", "login_otp_kyc", "account_blocked",
    "bank_linking", "app_performance", "ui_ux", "customer_support",
    "fraud_security", "rewards_cashback", "fees_charges", "ads_spam",
    "bills_recharge", "autopay_mandates", "investments_gold",
    "travel_booking", "general_praise", "uninformative",
]

BATCH_SIZE = 512
WAREHOUSE = r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb"


def main():
    with open(r"D:\projects\non-tech\data\interim\topic_classifier.pkl", "rb") as f:
        bundle = pickle.load(f)
    clf, mlb, model_name = bundle["clf"], bundle["mlb"], bundle["model_name"]

    con = duckdb.connect(WAREHOUSE)
    reviews = con.execute("SELECT review_id, review_text FROM main.stg_reviews").df()
    print(f"Classifying {len(reviews):,} reviews...")

    encoder = SentenceTransformer(model_name)

    all_review_ids = []
    all_probs = []
    n = len(reviews)
    for start in range(0, n, BATCH_SIZE):
        end = min(start + BATCH_SIZE, n)
        batch_texts = reviews["review_text"].iloc[start:end].fillna("").tolist()
        emb = encoder.encode(batch_texts, batch_size=64, show_progress_bar=False)
        probs = clf.predict_proba(emb)  # (batch, n_topics)
        all_review_ids.extend(reviews["review_id"].iloc[start:end].tolist())
        all_probs.append(probs)
        if (start // BATCH_SIZE) % 20 == 0:
            print(f"  {end:,} / {n:,} ({end/n*100:.1f}%)")

    all_probs = np.vstack(all_probs)
    preds = (all_probs >= 0.5).astype(int)  # matches the flat 0.5 threshold used in training/eval

    # Long format: one row per (review_id, topic) where predicted positive
    rows = []
    for i, review_id in enumerate(all_review_ids):
        for j, topic in enumerate(TOPICS):
            if preds[i, j] == 1:
                rows.append((review_id, topic, float(all_probs[i, j])))

    topics_df = pd.DataFrame(rows, columns=["review_id", "topic", "probability"])
    print(f"\nTotal (review, topic) positive pairs: {len(topics_df):,}")
    print(f"Reviews with at least one topic: {topics_df['review_id'].nunique():,} / {n:,}")

    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("DROP TABLE IF EXISTS raw.review_topics")
    con.execute("CREATE TABLE raw.review_topics AS SELECT * FROM topics_df")

    print("\nTopic prevalence across full corpus:")
    print(con.execute("""
        SELECT topic, COUNT(*) as n, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM main.stg_reviews), 2) as pct
        FROM raw.review_topics GROUP BY 1 ORDER BY 2 DESC
    """).df().to_string(index=False))

    con.close()
    print("\nSaved raw.review_topics to DuckDB.")


if __name__ == "__main__":
    main()

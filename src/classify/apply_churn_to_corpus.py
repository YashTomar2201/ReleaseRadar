"""Apply the trained churn_intent classifier to all 291K reviews,
saving raw.review_flags (review_id, churn_intent) to DuckDB.
competitor_mentioned is handled separately in Phase 7 (needs the fuller
alias-matching + relation classification, not just this binary flag).
"""
import pickle

import duckdb
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

BATCH_SIZE = 512
WAREHOUSE = r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb"


def main():
    with open(r"D:\projects\non-tech\data\interim\churn_classifier.pkl", "rb") as f:
        bundle = pickle.load(f)
    clf, model_name = bundle["clf"], bundle["model_name"]

    con = duckdb.connect(WAREHOUSE)
    reviews = con.execute("SELECT review_id, review_text FROM main.stg_reviews").df()
    print(f"Classifying churn_intent for {len(reviews):,} reviews...")

    encoder = SentenceTransformer(model_name)

    all_review_ids = []
    all_preds = []
    all_probs = []
    n = len(reviews)
    for start in range(0, n, BATCH_SIZE):
        end = min(start + BATCH_SIZE, n)
        batch_texts = reviews["review_text"].iloc[start:end].fillna("").tolist()
        emb = encoder.encode(batch_texts, batch_size=64, show_progress_bar=False)
        preds = clf.predict(emb)
        probs = clf.predict_proba(emb)[:, 1]
        all_review_ids.extend(reviews["review_id"].iloc[start:end].tolist())
        all_preds.extend(preds.tolist())
        all_probs.extend(probs.tolist())
        if (start // BATCH_SIZE) % 20 == 0:
            print(f"  {end:,} / {n:,} ({end/n*100:.1f}%)")

    flags_df = pd.DataFrame({
        "review_id": all_review_ids,
        "churn_intent": all_preds,
        "churn_probability": all_probs,
    })

    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("DROP TABLE IF EXISTS raw.review_flags")
    con.execute("CREATE TABLE raw.review_flags AS SELECT * FROM flags_df")

    n_churn = flags_df["churn_intent"].sum()
    print(f"\nPredicted churn_intent=true: {n_churn:,} / {n:,} ({n_churn/n*100:.2f}%)")
    print("Saved raw.review_flags to DuckDB.")
    con.close()


if __name__ == "__main__":
    main()

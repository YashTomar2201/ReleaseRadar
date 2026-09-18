"""Same technique as sample_rare_topic_boost.py, applied to churn_intent
specifically: only 8 positive training examples existed (dev+boost
combined), too thin for a reliable classifier. Keyword-guided sampling
for explicit leaving/switching/uninstalling language, excluding every
review_id already used anywhere (gold_sample + rare_topic_boost_sample)
so it can never overlap with the test split or double-count training
rows.
"""
import duckdb
import pandas as pd

N_SAMPLE = 150
SEED = 123

# Broad net -- many of these will turn out NOT to be true churn_intent
# on inspection (e.g. advising OTHERS to uninstall, not stating their
# own action), which is fine: negatives are still useful training
# signal for a binary classifier, and precision comes from the labeling
# step, not the keyword filter.
PATTERN = r"(uninstall|switch(ing)? to|switching|never use.*again|done with this app|deleting the app|delete this app|moving to|shifting to)"


def main():
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)
    exclude = pd.read_csv(r"D:\projects\non-tech\data\labels\gold_sample.csv")["review_id"].tolist()
    exclude += pd.read_csv(r"D:\projects\non-tech\data\labels\rare_topic_boost_sample.csv")["review_id"].tolist()
    exclude_list = "', '".join(exclude)

    pool = con.execute(f"""
        SELECT review_id, app_key, rating, review_text, text_length
        FROM main.stg_reviews
        WHERE regexp_matches(lower(review_text), '{PATTERN}')
          AND review_id NOT IN ('{exclude_list}')
    """).df()
    print(f"Candidate pool: {len(pool)}")

    n = min(N_SAMPLE, len(pool))
    sample = pool.sample(n=n, random_state=SEED).reset_index(drop=True)
    sample["split"] = "churn_boost"

    out_path = r"D:\projects\non-tech\data\labels\churn_boost_sample.csv"
    sample.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Sampled {len(sample)} candidates -> {out_path}")


if __name__ == "__main__":
    main()

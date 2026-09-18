"""Phase 7.2: extract candidate reviews mentioning a competitor app,
using the full alias list (not just the 3 tracked apps' own names --
BHIM, CRED, Amazon Pay, Navi, Supermoney, WhatsApp Pay all count as
"a competitor mentioned" even though we don't have review data FOR
those apps ourselves)."""
import re

import duckdb
import pandas as pd
import yaml

with open(r"D:\projects\non-tech\config\aliases.yaml") as f:
    ALIASES = yaml.safe_load(f)

# Compile one regex per app group, word-boundary-safe
PATTERNS = {}
for app, variants in ALIASES.items():
    escaped = [re.escape(v) for v in variants]
    PATTERNS[app] = re.compile(r"(?<![a-z])(" + "|".join(escaped) + r")(?![a-z])", re.IGNORECASE)


def find_mentions(text):
    if not isinstance(text, str):
        return []
    return [app for app, pat in PATTERNS.items() if pat.search(text)]


def main():
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)
    reviews = con.execute("""
        SELECT review_id, app_key, rating, review_text, review_date
        FROM main.stg_reviews
    """).df()
    con.close()

    print(f"Scanning {len(reviews):,} reviews for competitor mentions...")
    reviews["mentions"] = reviews["review_text"].map(find_mentions)
    # "Other apps mentioned" = mentions minus the reviewer's own app
    reviews["other_mentions"] = reviews.apply(
        lambda r: [m for m in r["mentions"] if m != r["app_key"]], axis=1)
    reviews["n_other_mentions"] = reviews["other_mentions"].map(len)

    candidates = reviews[reviews["n_other_mentions"] > 0].copy()
    candidates["other_mentions_str"] = candidates["other_mentions"].map(lambda x: ";".join(x))

    print(f"\nCandidates (mention >=1 OTHER app): {len(candidates):,} / {len(reviews):,} "
          f"({len(candidates)/len(reviews)*100:.2f}%)")
    print("\nBy reviewing app:")
    print(candidates.groupby("app_key").size())
    print("\nMost-mentioned competitor apps (counts, a review can mention >1):")
    from collections import Counter
    c = Counter()
    for lst in candidates["other_mentions"]:
        c.update(lst)
    for app, n in c.most_common():
        print(f"  {app:15s} {n:6,d}")

    out_cols = ["review_id", "app_key", "rating", "review_text", "review_date", "other_mentions_str", "n_other_mentions"]
    candidates[out_cols].to_csv(r"D:\projects\non-tech\data\interim\competitor_mention_candidates.csv",
                                 index=False, encoding="utf-8")
    print(f"\nSaved to data/interim/competitor_mention_candidates.csv")


if __name__ == "__main__":
    main()

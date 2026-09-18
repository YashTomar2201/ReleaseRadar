"""Phase 4.3: build the stratified 600-review sample for the gold label
set (150 dev + 450 test). Stratified by app x rating band (1-2 / 3 / 4-5),
equal-sized strata so rare bands (3-star is only ~3-4% of the corpus)
get enough examples for a meaningful accuracy check, and weighted toward
longer reviews within each stratum since short reviews carry little
topic signal (Phase 3 found 78-87% of reviews are <=5 words).

Output: data/labels/gold_sample.csv with columns
  review_id, app_key, rating, review_text, text_length, split (dev/test)
No topic labels yet -- those get filled in during the actual labeling
pass (AI-assisted per decision_log.md 2026-09-18, spot-checked blind by
the user on a subset).
"""
import duckdb
import numpy as np
import pandas as pd

RNG_SEED = 42
N_PER_STRATUM = 67  # 3 apps x 3 rating bands x 67 ~= 603, trimmed to 600
DEV_FRACTION = 0.25  # 150 dev / 450 test

RATING_BANDS = {
    (1, 2): "negative",
    (3, 3): "neutral",
    (4, 5): "positive",
}

def band_for_rating(r):
    for (lo, hi), name in RATING_BANDS.items():
        if lo <= r <= hi:
            return name
    return None


def main():
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)
    df = con.execute("""
        SELECT review_id, app_key, rating, review_text, text_length
        FROM main.stg_reviews
    """).df()
    df["rating_band"] = df["rating"].map(band_for_rating)

    rng = np.random.default_rng(RNG_SEED)
    picked = []

    for app in sorted(df.app_key.unique()):
        for band in ["negative", "neutral", "positive"]:
            pool = df[(df.app_key == app) & (df.rating_band == band)].copy()
            if len(pool) == 0:
                print(f"WARNING: no reviews for {app}/{band}")
                continue
            # Weight toward longer reviews: sampling weight = text_length,
            # softened with sqrt so we don't ONLY get the longest outliers.
            weights = np.sqrt(pool["text_length"].clip(lower=1).to_numpy())
            weights = weights / weights.sum()
            n = min(N_PER_STRATUM, len(pool))
            idx = rng.choice(pool.index.to_numpy(), size=n, replace=False, p=weights)
            sub = pool.loc[idx].copy()
            sub["stratum"] = f"{app}_{band}"
            picked.append(sub)
            print(f"{app}/{band}: pool={len(pool)}, sampled={n}, "
                  f"median_len={sub.text_length.median():.0f} (pool median={pool.text_length.median():.0f})")

    sample = pd.concat(picked, ignore_index=True)

    # Trim/pad to exactly 600 if strata rounding overshoots
    if len(sample) > 600:
        sample = sample.sample(n=600, random_state=RNG_SEED).reset_index(drop=True)

    # Stratified dev/test split: same proportion from each stratum
    sample["split"] = "test"
    for stratum in sample["stratum"].unique():
        idx = sample[sample.stratum == stratum].index.to_numpy().copy()
        rng.shuffle(idx)
        n_dev = max(1, round(len(idx) * DEV_FRACTION))
        sample.loc[idx[:n_dev], "split"] = "dev"

    sample = sample.sample(frac=1, random_state=RNG_SEED).reset_index(drop=True)  # shuffle final order

    out_cols = ["review_id", "app_key", "rating", "rating_band", "review_text", "text_length", "stratum", "split"]
    out_path = r"D:\projects\non-tech\data\labels\gold_sample.csv"
    sample[out_cols].to_csv(out_path, index=False, encoding="utf-8")

    print(f"\nTotal sampled: {len(sample)}")
    print(sample["split"].value_counts())
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()

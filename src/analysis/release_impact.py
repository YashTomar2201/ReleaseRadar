"""Phase 5: release-impact analysis via competitor-controlled
difference-in-differences with placebo tests.

Key design adaptation (see decision_log.md, 2026-09-18): the roadmap's
original placebo design assumed enough "quiet" calendar space to build
placebo dates that don't overlap ANY real release's window. With
PhonePe shipping a new version roughly every 12-16 days over our
~6-month window, a placebo exclusion buffer wide enough to avoid every
real release leaves ZERO candidate dates. Fixed by excluding only the
SPECIFIC release under test from its own placebo pool -- other real
releases may still fall inside some placebo windows, which makes the
null distribution noisier (wider) than a truly clean placebo would be.
This makes the significance test CONSERVATIVE (harder to call an effect
significant, not easier) rather than invalid -- documented explicitly,
not hidden.
"""
import warnings

import duckdb
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings("ignore")

FOCUS_APP = "phonepe"
CONTROL_APPS = ["gpay", "paytm"]
WINDOW = 21
ROLLOUT_BUFFER = (1, 2)  # exclude [d-1, d+2] as the staged-rollout period
MIN_WINDOW_DAYS = 7      # minimum pre/post days required to attempt a release
N_PLACEBO_MAX = 150
RNG_SEED = 2026
Q_THRESHOLD = 0.10


def load_panel(con):
    return con.execute("""
        SELECT app_key, review_date, negative_share, n_reviews
        FROM main.fct_daily_app_metrics
        WHERE is_complete_day
    """).df().assign(review_date=lambda d: pd.to_datetime(d.review_date))


def release_effect(panel, d, window=WINDOW):
    """Competitor-controlled DiD effect of a (real or placebo) event
    date d on negative_share. Returns None if there isn't enough data
    on both sides to fit the model."""
    pre_lo, pre_hi = d - pd.Timedelta(days=window), d - pd.Timedelta(days=ROLLOUT_BUFFER[0])
    post_lo, post_hi = d + pd.Timedelta(days=ROLLOUT_BUFFER[1]), d + pd.Timedelta(days=window)

    p = panel[((panel.review_date >= pre_lo) & (panel.review_date <= pre_hi)) |
              ((panel.review_date >= post_lo) & (panel.review_date <= post_hi))].copy()
    if p.empty:
        return None

    p["treated"] = (p.app_key == FOCUS_APP).astype(int)
    p["post"] = (p.review_date >= post_lo).astype(int)

    # Need variation on both sides for both treated and control groups
    focus = p[p.treated == 1]
    if focus.groupby("post").size().shape[0] < 2 or focus["post"].sum() < 3 or (focus["post"] == 0).sum() < 3:
        return None
    if p[p.treated == 0].groupby("post").size().shape[0] < 2:
        return None

    try:
        m = smf.wls("negative_share ~ treated:post + C(app_key) + C(review_date)",
                     data=p, weights=p["n_reviews"]).fit()
        key = [k for k in m.params.index if "treated:post" in k]
        if not key:
            return None
        return float(m.params[key[0]])
    except Exception:
        return None


def build_placebo_pool(panel, exclude_date, window=WINDOW):
    # Placebo dates must have a full pre/post window within the FOCUS
    # app's own date range (see the note in main() about why).
    focus_dates = panel.loc[panel.app_key == FOCUS_APP, "review_date"]
    min_d, max_d = focus_dates.min(), focus_dates.max()
    valid_start, valid_end = min_d + pd.Timedelta(days=window), max_d - pd.Timedelta(days=window)
    all_dates = pd.date_range(valid_start, valid_end)
    excl_lo, excl_hi = exclude_date - pd.Timedelta(days=window), exclude_date + pd.Timedelta(days=window)
    return [d for d in all_dates if not (excl_lo <= d <= excl_hi)]


def main():
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb")
    panel = load_panel(con)

    releases = con.execute("""
        SELECT review_version, adoption_date FROM main.int_version_adoption
        WHERE app_key = 'phonepe' ORDER BY adoption_date
    """).df()
    releases["adoption_date"] = pd.to_datetime(releases["adoption_date"])

    # NOTE: pre/post-availability bounds must use the FOCUS app's own
    # date range, not the cross-app panel range -- Google Pay's much
    # longer history (back to 2025-05) would otherwise make PhonePe's
    # earliest releases look like they have pre-period data they don't
    # actually have (PhonePe itself starts 2026-03-18).
    focus_dates = panel.loc[panel.app_key == FOCUS_APP, "review_date"]
    min_d, max_d = focus_dates.min(), focus_dates.max()
    rng = np.random.default_rng(RNG_SEED)

    results = []
    for _, row in releases.iterrows():
        d, version = row["adoption_date"], row["review_version"]
        pre_avail = (min(d - pd.Timedelta(days=ROLLOUT_BUFFER[0]), max_d) - max(d - pd.Timedelta(days=WINDOW), min_d)).days + 1
        post_avail = (min(d + pd.Timedelta(days=WINDOW), max_d) - max(d + pd.Timedelta(days=ROLLOUT_BUFFER[1]), min_d)).days + 1

        if pre_avail < MIN_WINDOW_DAYS or post_avail < MIN_WINDOW_DAYS:
            results.append({"version": version, "adoption_date": d, "n_pre_days": max(pre_avail, 0),
                             "n_post_days": max(post_avail, 0), "usable": False,
                             "real_effect": None, "n_placebo": 0, "placebo_p": None,
                             "q_value": None, "health_score": None, "is_significant": False})
            continue

        real_effect = release_effect(panel, d)
        if real_effect is None:
            results.append({"version": version, "adoption_date": d, "n_pre_days": pre_avail,
                             "n_post_days": post_avail, "usable": False,
                             "real_effect": None, "n_placebo": 0, "placebo_p": None,
                             "q_value": None, "health_score": None, "is_significant": False})
            continue

        placebo_pool = build_placebo_pool(panel, d)
        n_placebo = min(N_PLACEBO_MAX, len(placebo_pool))
        placebo_dates = rng.choice(placebo_pool, size=n_placebo, replace=False) if n_placebo > 0 else []

        placebo_effects = []
        for pd_ in placebo_dates:
            e = release_effect(panel, pd.Timestamp(pd_))
            if e is not None:
                placebo_effects.append(e)
        placebo_effects = np.array(placebo_effects)

        if len(placebo_effects) < 20:
            results.append({"version": version, "adoption_date": d, "n_pre_days": pre_avail,
                             "n_post_days": post_avail, "usable": False,
                             "real_effect": real_effect, "n_placebo": len(placebo_effects),
                             "placebo_p": None, "q_value": None, "health_score": None,
                             "is_significant": False})
            continue

        placebo_p = (np.sum(np.abs(placebo_effects) >= abs(real_effect)) + 1) / (len(placebo_effects) + 1)
        health_score = real_effect / placebo_effects.std() if placebo_effects.std() > 0 else np.nan

        results.append({
            "version": version, "adoption_date": d, "n_pre_days": pre_avail, "n_post_days": post_avail,
            "usable": True, "real_effect": real_effect, "n_placebo": len(placebo_effects),
            "placebo_p": placebo_p, "q_value": None, "health_score": health_score,
            "is_significant": False, "placebo_effects": placebo_effects,
        })

    results_df = pd.DataFrame(results)

    # Benjamini-Hochberg across releases WITH a computed p-value only
    scoreable = results_df["placebo_p"].notna()
    if scoreable.sum() > 0:
        reject, qvals, _, _ = multipletests(results_df.loc[scoreable, "placebo_p"], alpha=Q_THRESHOLD, method="fdr_bh")
        results_df.loc[scoreable, "q_value"] = qvals
        results_df.loc[scoreable, "is_significant"] = reject

    print(results_df.drop(columns=["placebo_effects"], errors="ignore").to_string(index=False))

    # Save placebo effects separately (for the histogram figure) before dropping
    placebo_store = {row["version"]: row.get("placebo_effects") for row in results
                      if row.get("placebo_effects") is not None}
    import pickle
    with open(r"D:\projects\non-tech\data\interim\placebo_effects.pkl", "wb") as f:
        pickle.dump(placebo_store, f)

    out = results_df.drop(columns=["placebo_effects"], errors="ignore")
    out.to_csv(r"D:\projects\non-tech\data\interim\release_impact.csv", index=False)
    print(f"\nSaved {len(out)} releases (usable={out['usable'].sum()}, "
          f"significant at q<{Q_THRESHOLD}: {out['is_significant'].sum()}) "
          f"to data/interim/release_impact.csv")
    con.close()


if __name__ == "__main__":
    main()

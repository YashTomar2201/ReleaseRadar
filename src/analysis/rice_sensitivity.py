"""Phase 8.5: sensitivity analysis. Effort estimates are a judgment
call (see issue_cost.py's EFFORT_WEEKS docstring), so test how much the
RICE ranking actually depends on them: vary each topic's effort by
+/-50% (Monte Carlo, 1000 runs) and report how often each issue stays
in the top 3 for its app."""
import numpy as np
import pandas as pd

N_RUNS = 1000
SEED = 7


def main():
    df = pd.read_csv(r"D:\projects\non-tech\data\interim\issue_backlog.csv")
    rng = np.random.default_rng(SEED)

    results = []
    for app in df["app_key"].unique():
        app_df = df[df.app_key == app].reset_index(drop=True)
        top3_counts = np.zeros(len(app_df), dtype=int)

        base_reach = app_df["reach"].to_numpy()
        base_impact = app_df["impact"].to_numpy()
        base_conf = app_df["confidence"].to_numpy()
        base_effort = app_df["effort_weeks"].to_numpy()

        for _ in range(N_RUNS):
            effort_noise = rng.uniform(0.5, 1.5, size=len(app_df))  # +/-50%
            sim_effort = base_effort * effort_noise
            sim_rice = (base_reach * base_impact * base_conf) / sim_effort
            top3_idx = np.argsort(-sim_rice)[:3]
            top3_counts[top3_idx] += 1

        app_df["top3_stability_pct"] = top3_counts / N_RUNS * 100
        results.append(app_df)

    out = pd.concat(results).sort_values(["app_key", "rice"], ascending=[True, False])
    print("=== Top-3 stability under +/-50% effort uncertainty (1000 Monte Carlo runs) ===")
    for app in df["app_key"].unique():
        print(f"\n--- {app} ---")
        print(out[out.app_key == app].head(6)[
            ["topic", "rice", "top3_stability_pct"]
        ].to_string(index=False))

    out.to_csv(r"D:\projects\non-tech\data\interim\issue_backlog_with_sensitivity.csv", index=False)
    print("\nSaved data/interim/issue_backlog_with_sensitivity.csv")


if __name__ == "__main__":
    main()

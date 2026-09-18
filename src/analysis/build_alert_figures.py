"""Phase 6 figures: (1) incident timeline for INC001 with detector
output marked, (2) false-alert rate summary across apps, (3) the
unconfirmed candidate signal timeline for transparency."""
import sys

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, r"D:\projects\non-tech\src\analysis")
from early_warning import load_hourly, add_detectors, merge_alert_events, BIN_HOURS
import duckdb

FIG_DIR = r"D:\projects\non-tech\reports\figures"


def main():
    con = duckdb.connect(r"D:\projects\non-tech\data\warehouse\releaseradar.duckdb", read_only=True)

    # --- Figure 1: INC001 timeline ---
    agg = load_hourly(con, "gpay", BIN_HOURS["gpay"])
    agg = add_detectors(agg, BIN_HOURS["gpay"])
    incident_start = pd.Timestamp("2025-08-07 19:45")
    first_report = pd.Timestamp("2025-08-07 20:15")
    window = agg[(agg.bin_start >= incident_start - pd.Timedelta(hours=24)) &
                 (agg.bin_start <= incident_start + pd.Timedelta(hours=24))]

    fig, ax = plt.subplots(figsize=(11, 5))
    colors = ['#d62728' if a else '#4285F4' for a in window['alert']]
    ax.bar(window.bin_start, window.n_negative, width=0.1, color=colors, label='negative reviews (3h bin)')
    ax.plot(window.bin_start, window.expected, color='gray', linestyle='--', label='expected (rolling baseline)')
    ax.axvline(incident_start, color='black', linestyle=':', linewidth=2, label='incident start (19:45)')
    ax.axvline(first_report, color='green', linestyle=':', linewidth=2, label='first public report (20:15)')
    ax.set_ylabel("Negative reviews per 3h bin")
    ax.set_title("INC001 (Google Pay, 2025-08-07): bin containing the incident alerted,\n"
                  "but bin-close latency (21:00) meant it LAGGED the public report by 45 min")
    ax.legend(fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/10_incident_timeline_inc001.png", dpi=130)
    print("Saved 10_incident_timeline_inc001.png")

    # --- Figure 2: false-alert rate per app ---
    rates = []
    for app, bin_hours in BIN_HOURS.items():
        a = load_hourly(con, app, bin_hours)
        a = add_detectors(a, bin_hours)
        events = merge_alert_events(a, bin_hours)
        n_weeks = (a.bin_start.max() - a.bin_start.min()).days / 7
        rates.append({"app": app, "bin_hours": bin_hours, "n_events": len(events),
                       "n_weeks": n_weeks, "events_per_week": len(events) / n_weeks})
    rates_df = pd.DataFrame(rates)
    print(rates_df.to_string(index=False))

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(rates_df.app, rates_df.events_per_week, color=['#5f259f', '#4285F4', '#00baf2'])
    ax.set_ylabel("Alert events per week")
    ax.set_title("False/total alert rate per app\n(no confirmed incidents to net out true positives for "
                  "PhonePe/Paytm -- reported as raw alert rate)")
    for i, row in rates_df.iterrows():
        ax.annotate(f"{row.events_per_week:.2f}/wk\n({row.bin_hours}h bins)", (i, row.events_per_week),
                    textcoords="offset points", xytext=(0, 5), ha='center', fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/11_alert_rate_per_app.png", dpi=130)
    print("Saved 11_alert_rate_per_app.png")

    con.close()


if __name__ == "__main__":
    main()

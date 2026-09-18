# ReleaseRadar — Power BI Build Guide

**What this is:** everything needed to assemble `releaseradar.pbix` from
the exported CSVs in `data/exports/` — relationships, DAX measures, and
a page-by-page spec. Power BI Desktop's report-building is a GUI-only
tool (no CLI/scripting surface for assembling visuals), so this guide
is written to be followed directly rather than auto-generated.

## 1. Import the data

Power BI Desktop → **Get Data → Text/CSV** → import every file in
`data/exports/`:

```
dim_date.csv              dim_app.csv               dim_topic.csv
dim_version.csv           fct_daily_app_metrics.csv fct_daily_topic_metrics.csv
fct_release_impact.csv    fct_alerts.csv            fct_switching.csv
fct_issue_backlog.csv     fct_review_samples.csv
```

Set each table's date/numeric columns' data types correctly on import
(Power BI usually infers these right, but double-check `review_date`,
`adoption_date`, `alert_start`/`alert_end` import as **Date/Time**, not
text).

## 2. Model view — relationships

All single-direction (dimension → fact), matching star-schema
convention:

| From | To | Notes |
|---|---|---|
| `dim_date[date]` | `fct_daily_app_metrics[review_date]` | |
| `dim_date[date]` | `fct_daily_topic_metrics[review_date]` | |
| `dim_app[app_key]` | `fct_daily_app_metrics[app_key]` | |
| `dim_app[app_key]` | `fct_daily_topic_metrics[app_key]` | |
| `dim_app[app_key]` | `fct_alerts[app_key]` | |
| `dim_app[app_key]` | `fct_issue_backlog[app_key]` | |
| `dim_app[app_key]` | `fct_review_samples[app_key]` | |
| `dim_app[app_key]` | `dim_version[app_key]` | |
| `dim_app[app_key]` | `fct_switching[source]` | **Active** |
| `dim_app[app_key]` | `fct_switching[dest]` | Inactive (see DAX below) |
| `dim_topic[topic_key]` | `fct_daily_topic_metrics[topic]` | |
| `dim_topic[topic_key]` | `fct_issue_backlog[topic]` | |
| `dim_topic[topic_key]` | `fct_review_samples[topic]` | |

**Note on `fct_release_impact` vs. `dim_version`:** `dim_version`
already has the release-impact fields joined in (`real_effect`,
`q_value`, `is_significant`) — use `dim_version` directly for the
Release Impact page rather than also relating `fct_release_impact`
separately (redundant; `fct_release_impact` is exported mainly for
direct SQL/Python reference outside Power BI).

**Note on the two `fct_switching` relationships:** DAX can't
auto-resolve which is "active" for a given visual, so the second
(inactive) relationship needs `USERELATIONSHIP()` in any measure that
needs the "as destination" direction — see `[Inflow Count]` below.

## 3. DAX measures

Create these in a dedicated measures table (Modeling → New Table →
`Measures = {BLANK()}`, or attach to `dim_app`) rather than scattering
them across import tables.

```dax
-- === Overview page ===

Total Reviews =
SUM ( fct_daily_app_metrics[n_reviews] )

Avg Rating =
DIVIDE (
    SUMX ( fct_daily_app_metrics, fct_daily_app_metrics[avg_rating] * fct_daily_app_metrics[n_reviews] ),
    [Total Reviews]
)

Negative Share =
DIVIDE (
    SUMX ( fct_daily_app_metrics, fct_daily_app_metrics[negative_share] * fct_daily_app_metrics[n_reviews] ),
    [Total Reviews]
)

Avg Rating 30D =
CALCULATE ( [Avg Rating], DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -30, DAY ) )

Avg Rating Prior 30D =
CALCULATE ( [Avg Rating], DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ) - 30, -30, DAY ) )

Rating Delta 30D =
[Avg Rating 30D] - [Avg Rating Prior 30D]

-- === Topic Explorer page ===
-- IMPORTANT: fct_daily_topic_metrics has NO total-reviews column of
-- its own by design -- the denominator must come from
-- fct_daily_app_metrics, or a topic-share sum would double count
-- (a review with 2 topics would count its day's total reviews twice).

Topic Reviews =
SUM ( fct_daily_topic_metrics[n_topic_reviews] )

Topic Share =
DIVIDE ( [Topic Reviews], [Total Reviews] )

-- === Release Impact page (use dim_version, not fct_release_impact) ===

Significant Releases =
CALCULATE ( COUNTROWS ( dim_version ), dim_version[is_significant] = TRUE () )

Usable Releases =
CALCULATE ( COUNTROWS ( dim_version ), dim_version[impact_analysis_usable] = TRUE () )

-- === Early Warning page ===

Alert Events =
COUNTROWS ( fct_alerts )

Alert Duration Hours =
AVERAGEX (
    fct_alerts,
    DATEDIFF ( fct_alerts[alert_start], fct_alerts[alert_end], HOUR )
)

-- === Competitive Switching page ===
-- fct_switching has TWO relationships to dim_app (source, dest); only
-- "source" is active by default, so the "as destination" measure needs
-- USERELATIONSHIP to force the inactive one.

Outflow Count =
SUM ( fct_switching[n] )   -- uses the active source-> relationship

Inflow Count =
CALCULATE (
    SUM ( fct_switching[n] ),
    USERELATIONSHIP ( dim_app[app_key], fct_switching[dest] )
)

Net Inflow =
[Inflow Count] - [Outflow Count]

-- === Fix Backlog page ===

Top3 Stability =
AVERAGE ( fct_issue_backlog[top3_stability_pct] )
```

## 4. Dashboard pages

Consistent theme: one fixed color per app across every page —
PhonePe `#5f259f`, Google Pay `#4285F4`, Paytm `#00baf2` (matches every
matplotlib figure already produced in `reports/figures/`, so screenshots
and the dashboard read as one system). Put an app slicer and a date
range slicer on every page (View → Sync Slicers).

### Page 1 — Executive Overview
- KPI cards: `[Avg Rating 30D]`, `[Rating Delta 30D]`, `[Negative Share]`,
  `[Alert Events]` (filtered to the selected period)
- Line chart: `Avg Rating` over `dim_date[date]`, one line per app
- Bar chart: top 5 issues by `fct_issue_backlog[rice]` for the selected app
- 3 text boxes with the headline findings (pull from `README.md`'s
  TL;DR once Phase 10 writes it)

### Page 2 — Topic Explorer
- Matrix/heatmap: `dim_app` × `dim_topic`, values = `[Topic Share]`
- Line chart: `[Topic Share]` trend for a topic selected via slicer
- Table with drill-through to `fct_review_samples` (right-click a
  topic/app/month cell → drill through to see example reviews)

### Page 3 — Release Impact
- Bar chart: `dim_version[real_effect]` (health-score-colored: use
  `is_significant` for conditional formatting), sorted by `adoption_date`
- Card: `[Significant Releases]` / `[Usable Releases]`
- Text box explaining the placebo-test methodology and the headline
  null result (see `reports/methodology.md`, Phase 5 section)

### Page 4 — Early Warning
- Table: `fct_alerts` sorted by `alert_start`, with `[Alert Duration Hours]`
- Card: the one validated incident (INC001) result, written as static
  text (a single case study doesn't need a dynamic visual)
- Bar chart: alert count per app (from Phase 6's
  `11_alert_rate_per_app.png` — can reuse as an image or rebuild natively)

### Page 5 — Competitive Switching
- Table or matrix: `fct_switching` (source, dest, n, per_10k)
- **Sankey diagram**: Power BI's built-in Sankey visual isn't in the
  default pane — go to **Insert → Get more visuals → search "Sankey"**
  (the free "Sankey Diagram" by Microsoft), then bind source/dest/n
- KPI cards: `[Net Inflow]` per app

### Page 6 — Fix Backlog
- Table: `fct_issue_backlog` sorted by `rice` descending, columns:
  topic, prevalence, penalty, churn_exposure, rice, top3_stability_pct
- Conditional formatting: highlight `needs_manual_review = TRUE` rows
  (the `ui_ux` caveat from Phase 8) in gray, not red/green like the rest
- Scatter chart: prevalence (x) vs. penalty (y), bubble size =
  `churn_exposure` (reproduces `15_issue_prevalence_vs_penalty.png`
  natively, so it's interactive/filterable by app)

## 5. Known data-quality notes to carry into the dashboard

- `is_complete_day = FALSE` rows exist in `fct_daily_app_metrics` /
  `fct_daily_topic_metrics` for each app's trailing ~2 days (Phase 1/3
  indexing-lag finding) — add a filter or visual-level warning so a
  viewer doesn't misread a real dip as a trend.
- `fct_release_impact` / `dim_version`: 0/12 usable releases are
  significant after correction — the Release Impact page should state
  this as the finding, not just show a chart without the conclusion.
- `fct_alerts`: only 1 confirmed incident validates recall; the rest of
  the alert history is unvalidated (false-alert-rate characterization
  only) — say so on the page, don't imply every alert is a real outage.
- `fct_switching`: counts are a lower bound (rule-based classifier,
  imperfect recall) — say so near the Sankey/table.

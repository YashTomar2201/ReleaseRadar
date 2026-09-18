# ReleaseRadar — Project Charter

## Problem
Product teams at UPI apps get thousands of reviews daily but can't easily
tell which releases hurt users, detect outages early, or prioritize fixes
by business impact. Public app-store reviews are a free, high-volume
signal that goes largely unused for this.

## Category & Apps
**Category:** UPI payments (India)

| App | Play Store ID | Role |
|---|---|---|
| PhonePe | `com.phonepe.app` | Focus app (deep-dive analyses) |
| Google Pay | `com.google.android.apps.nbu.paisa.user` | Competitor / control |
| Paytm | `net.one97.paytm` | Competitor / control |

**Why this category:** outages are publicly reported (NPCI/UPI issues get
news coverage) giving real incidents to validate the early-warning system
against; apps are direct competitors so switching behavior is common and
explicitly stated in reviews; review volume is very high (11M–24M reviews
per app), giving statistical power for daily/hourly analysis.

## Stakeholders (personas)
- **Product Manager, Payments** — wants release health + prioritized backlog
- **Head of Reliability / SRE** — wants early outage signals
- **Strategy / Growth** — wants competitive switching intelligence

## Key Questions
1. Which releases in the analysis window significantly changed user sentiment?
2. Can review signals detect outages earlier than public reporting?
3. What share of users threaten to switch, to which competitor, and why?
4. Which issues cost the most rating/churn, and what should be fixed first?

## Success Criteria
- Topic classifier: macro-F1 ≥ 0.75 on a held-out hand-labeled set
- Early warning: detect ≥ 70% of logged incidents with ≤ 1 false alert/app/week
- Release impact: every effect reported with a placebo-based p-value
- Deliverables: Power BI dashboard, 3 PM briefs, methodology doc, README

## Out of Scope
iOS App Store, non-English/non-Hinglish reviews (documented as a
limitation), real-time streaming pipeline (batch/weekly refresh only).

## Timeline
7 weeks, ~15–20 hrs/week. See [ROADMAP.md](../ROADMAP.md) for the full
phase-by-phase plan.

## Status
- [x] Phase 0 — Scoping & Setup
- [x] Phase 1 — Data Collection (291,200 reviews: PhonePe 101,600 / Google Pay 82,600 / Paytm 107,000; see decision_log.md for coverage windows and the ~24-25h review-indexing lag finding)
- [x] Phase 2 — Warehouse & dbt Staging Layer (stg_reviews, int_version_adoption, fct_daily_app_metrics; 22/22 dbt checks pass; release-date inference validated via PhonePe's build-date-encoded version strings -- see decision_log.md)
- [x] Phase 3 — Exploratory Data Analysis (notebooks/01_eda.ipynb, 6 figures, methodology.md "Data Quality & Coverage" section; caught & fixed the indexing-lag bug corrupting fct_daily_app_metrics)
- [x] Phase 4 — Topic Taxonomy, Labeling & Classification (codebook v1 via BERTopic; 600-review gold set + 120-review blind spot-check in progress; topic classifier macro-F1 0.556 after rare-topic boost; churn_intent classifier recall 0.615/precision 0.178; both applied to all 291K reviews -- see decision_log.md)
- [x] Phase 5 — Release Impact with Placebo Tests (12/15 releases usable; headline result: 0 significant after BH correction; top candidate investigated and found to be a parallel-trends artifact, not a real effect -- see decision_log.md)
- [x] Phase 6 — Early-Warning System (incident log much smaller than planned -- 1 confirmed, multi-sourced, in-window incident after extensive research; validated as a case study, not a powered recall estimate; alert lagged the public report by 45min due to the wider bin needed for GPay -- see decision_log.md)
- [x] Phase 7 — Brand-Switching Map (true competitor-mention rate 0.54%, much lower than Phase 3's inflated self-mention-including estimate; rule-based relation classifier validated at ~85-95% precision, imperfect recall; headline: PhonePe is the net beneficiary of switching among the 3 tracked apps -- see decision_log.md)
- [x] Phase 8 — Issue Cost & RICE Backlog (app_performance is #1 RICE-ranked issue for all 3 apps, 99-100% stable under effort-uncertainty Monte Carlo; ui_ux flagged for manual review -- positive rating coefficient; reach uses verified Play Store downloads as an MAU proxy -- see decision_log.md)
- [x] Phase 9 — dbt Marts + Power BI Dashboard (full star schema in dbt, 11 tables exported to CSV, DAX measures + page spec written in dashboards/POWERBI_BUILD_GUIDE.md -- actual .pbix assembly needs the user's own Power BI Desktop GUI session, no automation tool available for that -- see decision_log.md)
- [ ] Phase 10 — Storytelling & Packaging

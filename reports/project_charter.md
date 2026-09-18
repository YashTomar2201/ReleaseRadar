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
- [ ] Phase 3 — Exploratory Data Analysis
- [ ] Phase 4 — Topic Taxonomy, Labeling & Classification
- [ ] Phase 5 — Release Impact with Placebo Tests
- [ ] Phase 6 — Early-Warning System
- [ ] Phase 7 — Brand-Switching Map
- [ ] Phase 8 — Issue Cost & RICE Backlog
- [ ] Phase 9 — dbt Marts + Power BI Dashboard
- [ ] Phase 10 — Storytelling & Packaging

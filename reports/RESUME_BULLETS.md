# Resume Bullets — ReleaseRadar

Pick 2-3 depending on the role. All numbers are real, pulled directly
from this project's outputs (see `methodology.md` / `decision_log.md`
for the source of each).

## Full set (pick from these)

- Built an end-to-end analytics pipeline processing **291,200 Play
  Store reviews** across 3 competing UPI payment apps (Python, SQL,
  DuckDB, dbt — 74 automated data-quality tests), with a multi-label
  topic classifier reaching **macro-F1 0.556** after diagnosing and
  fixing a rare-class training-data shortage.
- Measured the **causal impact of 12 app releases** using
  competitor-controlled difference-in-differences with placebo tests
  and multiple-testing correction; found **0 significant results** —
  including investigating the one release that looked significant
  before correction and tracing it to a control-group artifact, not a
  real effect, preventing a false-positive finding from reaching a
  stakeholder.
- Built a **brand-switching intelligence map** from competitor mentions
  in review text (rule-based NLP classifier, ~85-95% precision,
  validated on a 183-review hand-checked sample); found the focus app
  gains a net **+0.94 to +1.66 switching mentions per 10K reviews**
  from each competitor, both driven by the same root cause identified
  in the competitor's own review data.
- Designed a **RICE-prioritized product fix backlog** from a rating-
  penalty regression and Monte Carlo sensitivity analysis (1,000 runs);
  identified one issue as the **#1 priority for all 3 competing apps
  independently**, stable in 99-100% of simulated effort-estimate
  scenarios.
- Built and validated a **review-based early-warning system** for
  service outages (Poisson + robust z-score anomaly detection on
  hourly/3-hourly bins); validated against an independently-confirmed,
  multi-sourced real incident and quantified the exact detection-speed
  trade-off of the time-bin width the data required.
- Uncovered a **competitive-intelligence finding requiring zero
  modeling**: one competitor replies to 96% of all reviews regardless
  of rating (blanket policy) while another replies to only 10% but
  precisely targets 1-star reviews (1.5★ avg for replied-to vs. 4.3★
  for the rest) — a clear signal of differing customer-support
  strategy, found through straightforward EDA.
- Designed a full star-schema data warehouse (dbt: 4 dimensions, 7 fact
  tables, 74 automated tests) and a complete Power BI dashboard
  specification (DAX measures, relationships, 6-page layout) from raw
  scraped data through to business-ready reporting.

## By role

**Data Analyst / Business Analyst**
> Built an end-to-end analytics pipeline processing 291,200 Play Store reviews (Python, SQL, DuckDB, dbt); measured the causal impact of 12 app releases via difference-in-differences with placebo tests and multiple-testing correction, correctly identifying 0 significant effects — including catching one false-positive-looking result before it became a wrong conclusion. Designed a RICE-prioritized fix backlog validated with Monte Carlo sensitivity analysis (1,000 runs), identifying one issue as the top priority across all 3 competing apps with 99-100% stability.

**Product Analyst**
> Measured the causal impact of 12 product releases using competitor-controlled difference-in-differences with placebo validation; built a brand-switching intelligence map from review-text NLP (~85-95% precision) showing the product's net competitive gain and its root cause; designed a RICE-prioritized backlog with sensitivity-tested rankings, identifying the #1 fix priority as stable across all 3 competing apps in 99-100% of simulated scenarios.

**BI / Analytics Engineer**
> Designed and built a full star-schema data warehouse in dbt (4 dimensions, 7 fact tables, 74 automated data-quality tests) from a custom Python scraping pipeline processing 291,200 reviews; built a complete Power BI dashboard specification (DAX measures, relationships, 6 pages) and a multi-label NLP classification pipeline (sentence embeddings + logistic regression, macro-F1 0.556) applied to the full corpus and materialized through the warehouse.

## Notes on framing

- The **release-impact null result** is a *feature*, not a weakness —
  say so directly in interviews: "I found and prevented a false
  positive" is a stronger signal of rigor than "I found something
  significant."
- The **1-incident early-warning validation** should be described
  honestly as a case study, not implied to be a statistically powered
  evaluation — interviewers who ask "how many incidents did you test
  against" deserve the real answer (one, after extensive research found
  most well-documented outages predate this project's data collection
  window) plus the false-alert-rate characterization that *is*
  statistically meaningful.
- If asked "what would you do with more time/budget": more labeled
  training data via a real LLM API (this project substituted targeted
  keyword-guided sampling due to no API budget), true MAU data instead
  of download-count proxies, and a longer collection window for a
  richer incident ground truth.

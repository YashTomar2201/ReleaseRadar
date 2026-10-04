# ReleaseRadar — Methodology

> Built incrementally as each phase completes. This is the document a
> skeptical interviewer's questions get answered from — see
> `decision_log.md` for the full reasoning trail behind each choice.

## Overview

This document covers, in build order: data collection and its real
limits (a Play Store pagination ceiling and a ~24-25h indexing lag that
silently corrupted two early models before being caught), EDA findings,
topic/churn classification and its honest accuracy numbers, causal
release-impact analysis (headline: a validated **null result**, not a
disappointing one), early-warning detection (validated against exactly
one independently-confirmed incident, not the larger set originally
planned), a brand-switching map (built on a corrected measurement — the
true competitor-mention rate turned out an order of magnitude lower
than an early estimate), an issue-cost/RICE backlog (with two
interpretive caveats caught before finalizing), and the Power BI
materials (with one real tooling limitation disclosed rather than
worked around).

**Running theme:** every phase surfaced at least one real problem —
a bug, a bad assumption, a measurement error, a design that didn't fit
the data — and every one is documented here as it was found and fixed,
not smoothed over in the retelling. The full turn-by-turn reasoning
trail is in `decision_log.md`; this document is the settled, readable
version of the same story.

## Data Collection

See `decision_log.md` (2026-09-18 entries) for full detail. Summary:
291,200 reviews scraped from the Play Store (PhonePe 101,600 / Google
Pay 82,600 / Paytm 107,000), newest-first, anonymized (SHA-256 hashed
usernames, no raw usernames stored). Coverage windows differ by app
because the Play Store's unofficial review API has a hard pagination
ceiling of ~80-110k reviews regardless of app velocity: PhonePe (~550
reviews/day) reaches only ~6 months of history before hitting it, while
Google Pay (~165/day) reaches ~16.5 months.

## Data Quality & Coverage (Phase 3 EDA)

**Coverage:** zero missing calendar days for any app across its full
collection window.

**Selection bias (rating distribution):** confirmed J-shaped/bimodal —
1-star and 5-star dominate, 2-4 star are comparatively rare (5-star
share: Paytm 77.0%, PhonePe 74.9%, Google Pay 66.7%; Google Pay's
1-star share, 17.8%, is notably higher than the other two). This is the
standard app-review selection-bias pattern: people review mostly when
delighted or angry. Every downstream metric (negative share, topic
share, RICE reach) should be read as a signal from the
reviewing-population, not a population-wide estimate — stated explicitly
here rather than corrected for, since there's no unbiased ground truth
to correct against with this data source alone.

**Text length:** 78-87% of reviews are 5 words or fewer across all three
apps (PhonePe highest at 87.4%). The topic classifier's real work is on
the informative minority; the `uninformative` codebook bucket will
absorb the majority of the corpus by count. Hand-labeling (Phase 4)
stratifies by length to ensure enough long/informative reviews are in
the gold set.

**Version coverage:** 10.4% (Google Pay) to 16.9% (PhonePe) of reviews
lack a `reviewCreatedVersion` tag. These are excluded from
`int_version_adoption` and any per-release analysis — not imputed, since
there's no reliable way to back out which version an untagged review
belongs to.

**Language mix:** an automated keyword-marker check (not a proper
language-ID model) found Hinglish tokens in a meaningful minority of
reviews across all three apps — enough that Phase 4's classifier must
handle code-mixed text explicitly (multilingual embeddings, an LLM
comfortable with Hinglish) rather than assuming English-only content.

**Time-of-day pattern:** a strong, consistent evening peak (~18:00-21:00
IST) and overnight trough (~02:00-05:00) across all three apps, matching
real payment-app usage patterns. This seasonality is strong enough that
Phase 6's early-warning detectors must baseline against the same
hour-of-week, not a flat threshold, or they would misfire on every
normal evening.

**Developer reply strategy (competitive-intelligence finding):** the
three apps have visibly different reply strategies. Paytm replies to
96.3% of all reviews regardless of rating (a blanket/templated policy —
avg rating when replied is 4.38★ vs. 4.27★ when not, barely different).
Google Pay replies to only 9.8% of reviews, but highly selectively:
replied reviews average 1.51★ vs. 4.31★ for non-replied — clear evidence
of targeted support outreach to angry reviewers. PhonePe sits in between
(29.9% reply rate; 3.79★ replied vs. 4.73★ not replied). This did not
require any modeling — a straightforward EDA cross-tab surfaced a real
difference in customer-support resourcing/strategy across competitors.

**A recurring data artifact (important methodological note):** the
Play Store API's ~24-25h review-indexing lag (found in Phase 1) does
not just mean "the last day is a bit incomplete" — it silently corrupted
two different downstream models before being caught:
1. `int_version_adoption` produced a spurious 349-day adoption gap for
   one PhonePe version, because a handful of stragglers on an old
   version could trivially cross the 5%-daily-share threshold on an
   artificially small final day.
2. `fct_daily_app_metrics` showed a dramatic same-day spike to 42-60%
   negative share for all three apps simultaneously on the final day,
   driven by sample sizes of only 10-19 reviews (vs. a normal
   170-650/day).

**Standard fix pattern adopted project-wide:** any daily-aggregation
model excludes, or flags via an `is_complete_day` boolean, the most
recent 2 days per app. Any new daily model added in later phases follows
this same convention.

**Genuine spike candidates surfaced (post-fix), for Phase 6's incident
log:**
- Google Pay, 2026-05-18/19: sustained 2-day elevation (38.2%, then
  37.5% negative) *and* elevated volume (774, then 325 reviews vs. a
  ~165/day average) — the combination suggests a real, widely-felt
  event.
- Paytm: a cluster of spike days in early May and mid-July 2026.
- Google Pay: several spikes within a 3-week window in April 2026.

**A regime shift, not just spike days, for Phase 5's release-impact
analysis to investigate directly:** Paytm's negative-share baseline
visibly shifts upward starting ~February-March 2026 — before that point
daily negative share mostly stays under 15%; after, it regularly spikes
above 20-40%, not just on isolated days. Google Pay shows a milder
version of the same pattern (elevated, noisier baseline roughly
Feb-June 2026).

Full analysis: [`notebooks/01_eda.ipynb`](../notebooks/01_eda.ipynb).
Figures: [`reports/figures/`](figures/).

## Topic Classification (Phase 4)

**Codebook:** 18 topics defined in `config/topics_codebook.md` (v1),
validated against BERTopic run on 25,000 real reviews before
hand-labeling began -- 3 topics (`autopay_mandates`, `investments_gold`,
`travel_booking`) were added based on real clusters the pre-data draft
missed. Multi-label: a review can carry more than one topic.

**Gold label set:** 600 reviews (150 dev / 450 test), stratified by
app x rating-band, weighted toward longer reviews. Labeled directly
against the codebook (`labeler=ai_v1`) -- see the "Gold-label method"
decision below for why this is disclosed as AI-assisted rather than
independent human labeling, and how it's being validated.

**Human validation:** a 120-review blind spot-check, sampled from the
test split, independently labeled and scored via Cohen's kappa against
the AI labels (`src/classify/score_spotcheck.py`).

**Spot-check result (120 reviews, one human labeler).** Headline is the
original, first-pass labeling; a corrected second pass follows below.
For the 8
topics with at least 5 human-positive examples, mean Cohen's kappa is
**0.71** and mean F1 **0.74** (rewards_cashback 0.955, general_praise
0.80, fraud_security 0.71, payment_failure 0.69, app_performance 0.66,
uninformative 0.64, customer_support 0.64, ui_ux 0.56). The other 10
topics have 0-4 positives in this sample, so their scores (including
the all-topic mean of 0.66) are not meaningful on their own. Patterns:
the AI over-tags `general_praise` (59 vs 47 human) and
`payment_failure` (16 vs 9, precision 0.56), and under-tags
`app_performance`, `customer_support`, `ui_ux` and `uninformative`
(recall 0.50-0.60). Single labeler, no second human, so this measures
agreement with one person rather than ground truth.

**Corrected second pass.** After the first score, 9 label slips found
by checks that did not use the AI labels were fixed: 4 reviews with no
topic at all (a plain "good" got `general_praise`; a UPI-ID feature
request got `ui_ux`; two failed or misrouted payments got
`payment_failure`) and 5 reviews where `general_praise` was dropped
because a specific topic was already tagged. Re-scored: mean kappa
**0.72**, mean F1 **0.76** (payment_failure 0.79, ui_ux 0.64,
general_praise 0.73). The `general_praise` drop is a convention
mismatch, not an error: the AI tags praise alongside the specific topic,
and the codebook wording on this is ambiguous. Original scores are kept
in `data/labels/spotcheck_results_original.csv`.

**Adjudicated third pass (made after seeing where the labels
disagreed with the AI's, so treat as optimistic).** 14 further edits,
each checked against the review text: removed `churn_intent` from 8
reviews that advise others to avoid the app, threaten an RBI or
consumer-court complaint, compare a feature to BHIM, mention an
uninstall prompt for a different app, or say the reviewer stayed because
of a card (the codebook requires an explicit statement of leaving);
removed `uninformative` from 2 reviews that name a specific issue;
removed one wrong `competitor_mentioned`; added `refund_delay` to 2
reviews and `login_otp_kyc` to 1. Result: mean kappa **0.73**, mean F1
**0.77** on the 8 topics with >=5 examples (uninformative now has 9).
`churn_intent` now has 1 human positive vs the AI's 2, so its kappa
(0.66) rests on 1-2 reviews and means nothing. Pass-2 files are kept as
`*_pass2.csv`.

**churn_intent disagreement in the first pass (kappa 0.35):** the human flagged 9
positives against the AI's 2. All 7 disagreements were reviews that
warn others off the app, threaten a consumer-court/RBI complaint, or
say "better to use other UPI apps", without an explicit statement of
uninstalling or switching. That is a definitional gap between the
labeler and the codebook rule, not clearly a classifier error, and it
is a reason to read `churn_intent` as a loose signal.

**Classifier:** multilingual sentence embeddings
(`paraphrase-multilingual-MiniLM-L12-v2`, chosen for Hinglish/Hindi
coverage -- the single largest BERTopic cluster, 12.5% of the sample,
was Hindi/Hinglish text) + one-vs-rest logistic regression.

| Iteration | Training rows | Macro-F1 (topics, ≥5 test examples) | Micro-F1 |
|---|---|---|---|
| Dev split only | 150 | 0.392 | 0.651 |
| + keyword-guided rare-topic boost | 374 | **0.556** | **0.686** |

Per-topic results in `data/labels/classifier_eval_results.csv`.
Weakest topics (`login_otp_kyc` 0.348, `ads_spam` 0.353,
`investments_gold` 0.364) should be read as directional in later
phases, not precise counts -- flagged explicitly rather than blended
into a single headline number.

**churn_intent:** a separate binary classifier (not folded into the
multi-label topic model), trained on 524 rows after a dedicated
keyword-guided boost (only 8 positive examples existed before it).
Evaluated on the same untouched 450-row test set: **recall 0.615,
precision 0.178, F1 0.276, kappa 0.242** -- tuned via
`class_weight='balanced'` to favor recall (catching more true signals)
over precision. Applied to the full corpus as `churn_probability` +
a 0.5-threshold flag; downstream analyses (Phase 7/8) should treat
`churn_intent=true` as "worth a closer look" given the false-positive
rate, not a confirmed signal on its own.

**Full-corpus application:** both classifiers applied to all 291,197
reviews (`src/classify/apply_classifier_to_corpus.py` and
`apply_churn_to_corpus.py`), loaded into DuckDB as `raw.review_topics`
(long format) and `raw.review_flags`, then staged in dbt as
`stg_review_topics` / `stg_review_flags` and aggregated into
`fct_daily_topic_metrics`.

**Topic prevalence, full corpus (291,197 reviews):** general_praise
77.4%, uninformative 19.5%, app_performance 6.5%, payment_failure 4.4%,
rewards_cashback 3.7%, fraud_security 3.3%, customer_support 2.7%,
ui_ux 2.4%, refund_delay 1.9%, autopay_mandates 1.6%, fees_charges 1.4%,
account_blocked 1.3%, bills_recharge 1.1%, login_otp_kyc 1.0%, ads_spam
0.9%, bank_linking 0.9%, investments_gold 0.8%, travel_booking 0.4%.
Directionally consistent with the 600-review gold set's proportions —
a useful sanity check that the classifier isn't systematically skewed.

## Release Impact (Phase 5)

**Method:** competitor-controlled difference-in-differences. For each
PhonePe release, PhonePe is the treated unit and Google Pay + Paytm are
controls; outcome is daily `negative_share`; model includes app and
date fixed effects; the 1-day-before to 2-day-after window around
adoption is excluded (staged-rollout period). Window: ±21 days where
available.

**Placebo design (adapted from the roadmap's original plan):** with
PhonePe shipping a release roughly every 12-16 days over a ~6-month
window, a placebo-date buffer wide enough to avoid every real release
leaves zero candidate dates. Fixed by excluding only the specific
release under test from its own placebo pool — this makes the
significance test **conservative** (other real releases can still
land in some placebo windows, widening the null distribution) rather
than invalid, and is disclosed as such rather than silently changing
the method without comment.

**Coverage:** 15 tracked PhonePe releases; 3 excluded for insufficient
pre/post data (the earliest 2 have zero pre-period, the most recent has
4 days of post-period); **12 usable**.

**Headline result: 0 of 12 releases are significant after
Benjamini-Hochberg correction (q<0.10).** The strongest candidate
(`26.05.08.0`, health score 4.58, uncorrected p=0.010) does not survive
correction (q=0.122) — and on investigation with a second, independent
method (comparing old vs. new version ratings on the *same calendar
days* during rollout, which needs no competitor comparison at all), no
corroborating effect was found (+0.056 rating difference, p=0.270, wrong
sign). Root cause: both control apps moved substantially during this
specific comparison window (Google Pay -5.6pp, Paytm -6.2pp negative
share) while PhonePe stayed flat (+1.1pp) — a parallel-trends
violation from two apps that are highly volatile throughout the whole
window, not a clean step change. This is treated as noise in volatile
control series, not attributed to a specific named incident without
independent confirmation, even though the timing is close to the
Phase 3 EDA's Google Pay 2026-05-18/19 spike.

**Why a null result is a legitimate finding here, not a failed
analysis:** a DiD estimate without placebo testing, multiple-testing
correction, and a corroborating second method would have reported
`26.05.08.0` as a confirmed negative release effect — exactly the kind
of false positive this validation stack exists to catch. The
methodologically correct conclusion for this window is that no PhonePe
release shows robust evidence of a negative causal impact on review
sentiment, which is itself informative about release-quality stability
and demonstrates the value of full causal validation over a single
p-value.

Full results: `data/interim/release_impact.csv`. Figures:
`07_release_health_scores.png`, `08_placebo_histogram_top_candidate.png`,
`09_diagnostic_parallel_trends.png`.

## Early-Warning System (Phase 6)

**Method:** N-hour bins per app (PhonePe 1h — highest volume; Google
Pay/Paytm 3h — thinner hourly volume, per the Phase 4-era data-
sufficiency decision), two detectors combined with OR: a Poisson test
on negative-review counts against an hour-of-day rolling baseline
(14-day lookback, leakage-safe via `.shift(1)`), and a robust
(MAD-based) z-score against the same baseline. Adjacent alert bins
within 3 hours are merged into episodes.

**Incident log — much smaller than planned, and why.** ~15 web
searches plus direct verification against Wikipedia's "Unified
Payments Interface" article and its citation list found several
well-documented UPI outages (12 April 2025, 26 March 2025, 2 April
2025, 12 May 2025) — but every one of them predates every app's actual
data-collection window (Google Pay from 2025-05-04, Paytm from
2025-10-13, PhonePe from 2026-03-18). This is a real asymmetry: this
project collects data close to real time, and well-established
historical incidents are naturally better-covered retrospectively than
very recent ones. Two search-summary date misattributions were caught
and corrected by checking a primary source's URL date pattern directly
rather than trusting the tool's natural-language summary.

**Exactly one incident** is both independently multi-sourced (4
citations via Wikipedia: two Economic Times articles, Hindustan Times,
Financial Express) and falls inside a reviewable window: **INC001,
2025-08-07 ~19:45 IST**, a UPI-wide outage attributed by NPCI to
bank-side technical issues (HDFC, SBI, Bank of Baroda, Kotak
Mahindra) — usable only against Google Pay's data.

**With n=1, a recall/precision percentage would be statistically
meaningless** — reported instead as a validated single case study,
plus a false-alert rate (which *is* meaningful with many quiet
periods) and an exploratory, clearly-unconfirmed check against the
Phase 3 EDA's own candidate signal.

**Case study result:** the 3-hour bin containing the incident's own
start time (18:00-21:00) correctly alerted (16 vs. ~7 expected negative
reviews at 12:00, then 15 vs. ~7 at 18:00 — both far above baseline).
But using the realistic detection time for a batch-processed system
(bin close, 21:00) rather than the bin's start, the alert **lagged the
public report (20:15) by 45 minutes** rather than beating it. Honest
takeaway: the wider bin adopted specifically because Google Pay's
hourly volume was too thin for reliable 1-hour detection trades away
speed for statistical reliability — in this specific case, that
trade-off meant not beating the news.

**False-alert rate** (raw, since only Google Pay has a confirmed
incident to net out): PhonePe 1.12/week (1h bins), Google Pay 0.70/week
(3h bins), Paytm 1.33/week (3h bins).

**Exploratory, unconfirmed:** the detector also fires on the Phase 3
EDA's Google Pay 2026-05-18/19 candidate signal — expected, since it's
the same underlying data, not independent validation. A dedicated news
search for this specific date found no corroborating coverage; reported
as an unconfirmed candidate, not a second validated incident.

Outputs: `data/interim/alert_events.csv` (143 total events across 3
apps), loaded as `fct_alerts`. Figures: `10_incident_timeline_inc001.png`,
`11_alert_rate_per_app.png`.

## Brand-Switching Map (Phase 7)

**Competitor mentions:** extracted using the full `config/aliases.yaml`
variant list, explicitly excluding a review mentioning its *own* app
(a PhonePe review saying "phonepe" isn't a competitor mention). True
rate: **0.54%** (1,578 / 291,197 reviews) — an order of magnitude
lower than Phase 3's rough 3.4-7.9% estimate, which hadn't excluded
self-mentions and was therefore dominated by an app's own name
appearing in its own reviews. This correction is logged in
decision_log.md, 2026-09-19.

**Relation classification:** rule-based regex classifier (not a full
ML pipeline — 1,578 candidates doesn't justify one the way the
291K-review topic corpus did) into `switching_away` /
`switched_from_competitor` / `comparison_only` / `none`. Manually
validated on a 183-review stratified sample: **precision on positive
predictions was good** (~85-90% switching_away, ~95% comparison_only,
3/3 correct for the rare switched_from_competitor class), but **recall
had real gaps** — roughly 40-50% of "none" predictions were, on
inspection, true relations the regex missed (phrasing variants,
adverbs breaking rigid word-adjacency, and Hindi/Hinglish comparisons
missed entirely by English-only patterns). Fixed the cheap, well-
justified gaps and re-ran (comparison_only 358→466, switching_away
115→157); spot-checked that about half the originally-identified
misses are now caught, with the rest needing increasingly specific
patterns for diminishing returns. **These counts are a lower bound on
true switching signal, not an exhaustive count** — stated explicitly
rather than presented as complete.

**Switching matrix:** flow direction from `switching_away` (source =
reviewing app) and `switched_from_competitor` (source = the app named,
dest = reviewing app) rows. Rates per 10k reviews, with bootstrap 95%
CIs (1,000 resamples), computed only where the source is a tracked app
(PhonePe/Google Pay/Paytm) — flows from untracked competitors (BHIM,
CRED, etc.) as source have no denominator and are reported as raw
counts only.

**Headline finding: PhonePe is the net beneficiary** of switching
among the three tracked apps — net flow toward PhonePe from both
Google Pay (+0.94/10k) and Paytm (+1.66/10k); Google Pay and Paytm are
roughly balanced with each other (+0.12/10k, not clearly distinguishable
given overlapping CIs). Google Pay shows the most *outflow* mentions
overall (to PhonePe, BHIM, Amazon Pay, and Paytm combined) — consistent
with Phase 3's finding of its higher 1-star share.

**Reasons behind the two largest flows into PhonePe:** both are
dominated by `app_performance` complaints on the app being left —
Google Pay→PhonePe (n=24): app_performance (8), customer_support (5),
account_blocked (5); Paytm→PhonePe (n=21): app_performance (13, 62% of
this flow), customer_support, fraud_security.

Outputs: `data/interim/switching_matrix.csv`,
`data/interim/relation_classified.csv`, loaded as `fct_switching`.
Figures: `12_switching_heatmap.png`, `13_outflow_by_app.png`,
`14_switching_reasons.png`.

## Issue Cost & RICE Backlog (Phase 8)

**Rating-penalty regression:** OLS with robust (HC1) standard errors,
`rating ~ topic_dummies + app + month + log(text_length)`, fit on all
291,197 reviews. Every topic except `ui_ux` and `bills_recharge` has a
significant negative penalty; `app_performance` is the largest
(-1.32★), `bills_recharge` is not significant (-0.003, p=0.90).

**`ui_ux` has a positive coefficient (+0.375, p<0.001)** — the one
exception, and deliberately not smoothed over. Investigation traced it
to Phase 4 labeling: `ui_ux` was frequently co-tagged with
`general_praise` (constructive feature requests from otherwise-happy
reviewers, not pure complaints). Flagged in the output
(`needs_manual_review=true`) and excluded from the automated top-list
interpretation rather than silently ranked by `abs(penalty)` like every
other topic.

**Issue Cost Index:** `rating_lift_if_fixed = prevalence × |penalty|`,
`churn_exposure = prevalence × churn_intent_rate`, computed per (app,
topic) over the trailing 90 days of complete data.

**RICE:** Reach uses **Play Store download counts** (PhonePe/Paytm
500M+, Google Pay 1B+ — verified Phase 0) as a proxy for MAU, not true
MAU itself — third-party "MAU" statistics found via search were
inconsistent across sources (some from content-mill sites, not primary
reporting) and were not trustworthy enough to hard-code into the
analysis. This means **within-app ranking is methodologically sound;
cross-app RICE comparison is not** — Google Pay's higher scores
partly reflect its 2x larger download count, not necessarily more
severe issues. Impact mapped from rating lift to a 0.25/0.5/1/2/3
scale; Confidence from the Phase 4 classifier's per-topic F1; Effort
in person-weeks is an explicit judgment call (documented per-topic in
`issue_cost.py`), not derived from data.

**Sensitivity analysis:** Monte Carlo (1,000 runs) varying each
topic's effort ±50%, reporting how often it stays in the app's top 3.
`app_performance` is essentially guaranteed to stay #1 (99-100%
stability across all 3 apps) regardless of effort uncertainty; ranks
below #1 are genuinely sensitive to the effort assumption (as low as
17-23% stability for some topics) — reported honestly rather than
implying a precise, stable rank order below the clear #1.

**Headline finding: `app_performance` is the #1 RICE-ranked issue for
all 3 apps independently** — robust to both the ui_ux caveat and the
reach-scale caveat above, and the most statistically stable ranking in
the entire backlog.

Outputs: `data/interim/issue_backlog_with_sensitivity.csv`,
`data/interim/rating_penalties.csv`, loaded as `fct_issue_backlog`.
Example reviews: `reports/briefs/issue_backlog_examples.txt`. Figure:
`15_issue_prevalence_vs_penalty.png`.

## dbt Marts & Power BI (Phase 9)

**Star schema completed in dbt:** `dim_date`, `dim_app`, `dim_topic`,
`dim_version` (with Phase 5 impact fields joined in), plus the 6 fact
marts built across Phases 3-8 (`fct_daily_app_metrics`,
`fct_daily_topic_metrics`, `fct_release_impact`, `fct_alerts`,
`fct_switching`, `fct_issue_backlog`) and a bounded, anonymized
`fct_review_samples` for drill-through (5,182 rows — never the full
291K-review corpus). All 74 dbt checks pass.

**A real tooling limit, disclosed rather than worked around:** Power BI
Desktop's report canvas is GUI-only with no scriptable/CLI surface, and
this environment has no automation tool for arbitrary Windows desktop
apps. Everything programmatically buildable is done — the star schema,
all 11 tables exported to `data/exports/`, and the complete
relationship/DAX-measure/page-by-page specification in
`dashboards/POWERBI_BUILD_GUIDE.md` — but the final visual assembly
into a `.pbix` requires a hands-on Power BI Desktop session, documented
as a clear, mechanical handoff rather than skipped or faked.

`sql/analysis_queries.sql`: 6 reference queries (window functions,
QUALIFY, percentiles, a cohort-style first-topic analysis) validated
directly against the warehouse, demonstrating SQL beyond what the dbt
pipeline itself needed.

# Decision Log

> Running log of choices made and why. This is the raw material for
> interview answers — every "why did you..." question should have an
> entry here.

## 2026-09-17 — Phase 0

**Decision:** Category = UPI payments; apps = PhonePe (focus), Google Pay,
Paytm.
**Why:** UPI outages are publicly reported with timestamps (needed for
Phase 6 early-warning validation), the three apps are direct competitors
so switching is common and explicit in review text (Phase 7), and review
volume is very high (11M–24M per app per Play Store listing), giving
statistical power for daily/hourly analysis (Phases 5–6).
**Alternatives considered:** quick commerce (Blinkit/Zepto/Instamart) —
stronger switching signal and hiring demand, but outages are rarely
publicly timestamped, which would weaken the early-warning validation
(the strongest planned result). Stock trading apps (Zerodha/Groww/Upstox)
— arguably the single strongest category (precise outage timestamps
during market hours, high business stakes) but smaller/less relatable
user base. UPI chosen as the strongest balance across all four Tier-1
components; trading apps or quick commerce are good follow-on categories
to rerun the pipeline against later, given it's built to be reusable.

**Decision:** App IDs verified directly against live Play Store listings
(not taken from memory) before locking them into config.
**Why:** package IDs are easy to get wrong (e.g. Google Pay's ID does not
contain "gpay"), and a wrong ID silently scrapes nothing or the wrong app.
**Verified (2026-09-17):**
- PhonePe → `com.phonepe.app` (4.4★, 14.2M reviews, 500M+ downloads)
- Google Pay → `com.google.android.apps.nbu.paisa.user` (4.3★, 11.4M reviews, 1B+ downloads)
- Paytm → `net.one97.paytm` (4.7★, 24.2M reviews, 500M+ downloads)

**Decision:** Repository structure follows the layered
raw → staging → intermediate → marts convention (dbt) and mirrors it in
`data/` and `src/`.
**Why:** matches how real analytics engineering teams organize projects;
demonstrates the convention explicitly in interviews.

**Decision:** `.gitignore` excludes all of `data/raw/`, `data/warehouse/`,
`data/interim/`, `data/exports/` but explicitly keeps `data/labels/`
tracked.
**Why:** raw scraped data and the DuckDB warehouse are large,
regeneratable from the scraper, and reviewer content shouldn't sit in a
public git history even hashed; hand-labeled gold-set labels are small,
not regeneratable without redoing hours of manual work, and are core
project evidence — they must be committed.

## 2026-09-17/18 — Phase 1: pagination depth test

**Finding:** ran a depth test pulling PhonePe reviews (newest-first,
lang=en, country=in) continuously to find the Play Store's real
pagination limit. It exhausted naturally (empty batch, not a stall) at
**93,200 unique reviews**, covering **169 days** (2026-03-30 to
2026-09-16), i.e. ~5.6 months of history at ~551 reviews/day. Took 4,506s
(~75 min) of continuous scraping at batch_size=200, sleep=0.3s.
**Implication:** `max_reviews_per_app: 300000` in `config/apps.yaml` is
not achievable for a high-volume app scraped this way — the Play Store's
own pagination caps it well below that regardless of the ceiling we set.
~90-100k reviews / ~5-6 months appears to be the practical ceiling for
PhonePe; other apps may differ based on their own review velocity.
Lowered `max_reviews_per_app` to 150,000 as a safety ceiling the scraper
will never actually hit — the real stopping condition is the Play
Store's own empty-batch response.
**~5.6 months is enough runway** for the planned analyses: release-impact
windows are ±21 days per release, and the early-warning system needs
weeks (not months) of hourly baseline per topic. It does mean fewer
distinct historical releases will be analyzable than if we had a full
year — noted as a limitation to state explicitly in the methodology doc.

**Bug found:** the immediately following Google Pay scrape returned an
**empty batch on its very first request** (before any reviews were
collected), most likely a transient rate-limit after ~75 minutes of
continuous requests to the same upstream API. The throwaway test script
treated any empty batch as "pagination exhausted" and crashed trying to
build a DataFrame from zero rows. **Fixed in the production scraper**
(`src/scrape/scrape_reviews.py`): an empty batch is only treated as
genuine pagination exhaustion when reviews have already been collected
for that app (`total > 0`); an empty *first* batch is instead treated as
a transient failure and retried with backoff. Added a cooldown between
apps (60s) to reduce the chance of one app's scrape rate-limiting the
next.
**Result / what I'd check next:** re-run Google Pay alone after the fix
to confirm it was transient and not an actual per-app restriction.

## 2026-09-18 — Phase 1: full scrape results

**Result:** full production scrape completed for all 3 apps using the
fixed scraper (retry-on-empty-first-batch + 60s inter-app cooldown).

| App | Reviews collected | History reached | Runtime |
|---|---|---|---|
| PhonePe | 101,600 | back to 2026-03-18 (~6 months) | 573s |
| Google Pay | 82,600 | back to 2025-05-04 (~16.5 months) | 1,031s |
| Paytm | 107,000 | back to 2025-10-13 (~11 months) | 789s |

All three exhausted via a genuine empty batch (not a stall/retry), and
all `reviewId`s are unique within each app — no duplicate collection in
this single run. Missing `reviewCreatedVersion` share: gpay 10.4%,
paytm 14.2%, phonepe 16.9% — will need to be handled in the release-date
inference logic (Phase 2) and reported as a data-quality note (Phase 3).
Loaded into `raw.reviews` in DuckDB via `src/load/load_raw.py` (fixed a
bug where the loader's summary query used the unquoted column `at`,
which is a reserved keyword in DuckDB SQL and must be double-quoted).

**Confirms the depth-test pattern from 2026-09-17:** the Play Store's
unofficial review API caps out at roughly the same *page count*
(~400-535 pages / ~80-110k reviews) regardless of the app's review
velocity — a high-velocity app (PhonePe, ~550 reviews/day) hits that
page-count ceiling in only ~6 months of history, while a lower-velocity
app (Google Pay) reaches back over 16 months before hitting the same
ceiling. This means the three apps have **unequal historical windows**,
which is fine for cross-sectional/competitor-control analyses (Phase 5's
difference-in-differences only needs overlapping windows around each
PhonePe release) but means Google Pay-specific historical analysis has
much deeper history available than Paytm or PhonePe.

## 2026-09-18 — Phase 1: discovered a ~24-25h review-indexing lag

**Finding:** checked whether `at` (the review's posted timestamp) is in
a sane timezone by comparing it against `scraped_at` (our own system
clock at collection time, IST) for the very first page fetched per app —
i.e. the freshest reviews the API could possibly return at the moment of
the call. Even for that first page, the **minimum** gap between
`scraped_at` and `at` was **24.3-24.8 hours across all three apps**
(median 31-34h, since a 200-row page spans several hours of postings).
**This is not a timezone artifact** (real timezone offsets cap at ~14h) —
it is a systematic indexing/caching lag in the unofficial Play Store
review API: a review appears on the live Play Store page for other users
almost immediately, but does not become retrievable via this scraping
method for roughly a day.
**Why this matters for Phase 6 (early-warning system):** the project's
early-warning analysis uses each review's own `at` timestamp as ground
truth for "when the user experienced/reported the issue" — that part of
the analysis (recall, lead time vs. the incident log) stays valid and
historically honest, since it's asking "would a system watching review
content, at normal latency, have caught this early" using real posting
times. But it means **this specific collection method (unofficial
scraper) could not itself be deployed as a live, low-latency production
alerting system** — a real deployment would need either the app owner's
own Google Play Console API access or a paid third-party review-
monitoring API with faster indexing. I will state this distinction
explicitly in the Phase 6 write-up and the methodology doc: the analysis
validates that the *signal* in review content precedes public incident
reports, not that *this pipeline as built* achieves sub-day latency.
**Secondary uncertainty:** cannot fully rule out that part of the ~24h
gap is `at` being reported in UTC while `scraped_at` is naive local IST
(UTC+5:30) — if so the true minimum lag would be closer to ~19h rather
than ~24h. Either way the finding (a lag measured in **hours-to-a-day**,
not minutes) and its implication for Phase 6 hold regardless of the
exact figure. Will revisit if an independently-dated real incident
(Phase 6) gives a cleaner anchor for the true timezone/offset.

## 2026-09-18 — Data sufficiency check across all planned analyses

**Checked real volume against each phase's statistical needs before
committing further, rather than assuming the roadmap's generic targets
were automatically met.**

- Release impact (Phase 5): PhonePe has 22 versions with ≥200 reviews,
  Paytm 38, Google Pay 74 — far more candidate releases than needed.
  PhonePe alone averages 552 reviews/day, giving strong power for
  ±21-day DiD windows. **Sufficient, no change needed.**
- Switching (Phase 7): direct regex scan for competitor names found
  3,442 (PhonePe, 3.4%), 6,534 (Google Pay, 7.9%), 7,298 (Paytm, 6.8%)
  candidate mentions — ~17,300 combined, well above the earlier rough
  estimate of 1-3%. **Sufficient, no change needed.**
- Issue cost / RICE (Phase 8): 291K total reviews gives stable rating-
  penalty regression coefficients even for topics at 1-2% prevalence.
  **Sufficient, no change needed.**
- **Early warning (Phase 6) — genuine weak spot.** Hourly averages:
  PhonePe 23.7 reviews/hr (2.22 negative), Paytm 14.0 (1.78), Google Pay
  7.4 (1.54). A per-topic hourly count (a fraction of the negative
  count) would be under 1/hour for Google Pay, too thin for reliable
  Poisson-based spike detection at that granularity -- real signal
  would need to be a large, sudden spike to separate from noise.
  **Design change made before building Phase 6:** widen the detection
  bin to 2-3 hours for Google Pay and Paytm; keep PhonePe (highest
  volume, and the focus app) at hourly resolution where the roadmap's
  original hourly design still holds. Treat PhonePe as the primary
  early-warning validation case and Google Pay/Paytm as secondary for
  this component specifically -- state this explicitly in the Phase 6
  write-up rather than reporting one blended recall/lead-time number
  across apps with very different statistical power.

## 2026-09-18 — Phase 2: release-date inference validated (better than planned)

**Result:** `int_version_adoption` infers 15 analyzable PhonePe releases
(200+ reviews, 5% daily-share threshold). Validation approach changed
from the roadmap's plan (spot-check ~10 dates against APKMirror) because
**PhonePe is not listed on APKMirror at all** -- a direct search and a
forced "search anyway" both returned zero results. This is itself a
believable finding: PhonePe, like several Indian fintech/banking apps,
appears to restrict third-party APK distribution, likely for
anti-tampering/compliance reasons (unverified assumption, but consistent
with the total absence of any listing).

**Better validation found instead:** PhonePe's version strings
themselves encode a build date (`YY.MM.DD.build`, e.g. `26.07.03.0` =
built 2026-07-03). This gives an exact, comprehensive cross-check
instead of a handful of manual spot-checks: compared the inferred
`adoption_date` (first day a version reaches 5% of daily reviews)
against the version's own embedded build date for all 15 releases.
**Result: a tight, consistent gap of 13-33 days (median 17, mean 17.4,
std 5.1)** between build and adoption -- exactly the pattern expected
from Google Play's staged rollout process (build → staged rollout start
→ time to reach 5% of the actively-reviewing population). This is
stronger evidence of correctness than the originally planned approach:
exact dates, full coverage (15/15 releases), not an approximate
eyeballed comparison on ~10.

**Bug found and fixed via this check:** the first version of the model
produced one clearly wrong adoption date -- version `25.10.03.0` (built
2025-10-03) got `adoption_date = 2026-09-17`, a 349-day gap, wildly
outside the pattern every other release showed. Root cause: that was
the very last day in the dataset, which has an incomplete review count
due to the ~24-25h indexing lag found in Phase 1 -- making the 5%
share threshold trivially easy to cross by a handful of stragglers on
an old version. **Fix:** `int_version_adoption` now excludes the most
recent 2 days per app from the share calculation (see the model's SQL
comment). Re-running confirmed the artifact is gone and the remaining
15/15 releases all fall in the expected 13-33 day range.
**Why this matters beyond this one bug:** the Phase 1 indexing-lag
finding wasn't just a footnote -- it caused a concrete, silent error
in a downstream model, and would likely cause similar edge effects in
any other daily-aggregation model (e.g. `fct_daily_app_metrics`) if the
last 1-2 days are treated as complete. Worth remembering when writing
Phase 3 EDA and any daily-trend chart: flag or exclude the last ~2 days
per app as provisional.

## 2026-09-18 — Phase 3: EDA complete, one more instance of the indexing-lag bug found and fixed project-wide

Full write-up lives in `reports/methodology.md` ("Data Quality &
Coverage" section) and `notebooks/01_eda.ipynb` -- not duplicated here.
Headline items:
- Confirmed J-shaped rating distribution; Google Pay's 1-star share
  (17.8%) notably higher than PhonePe (7.7%) / Paytm (11.2%).
- 78-87% of reviews are <=5 words -- carried into Phase 4 labeling
  strategy (stratify by length).
- **Caught the Phase 1 indexing-lag bug corrupting a SECOND model**
  (`fct_daily_app_metrics` showed a same-day 42-60% negative-share spike
  for all 3 apps simultaneously, driven by 10-19-review samples on the
  final day). Fixed by adding an `is_complete_day` flag, matching the
  pattern already used in `int_version_adoption`. Adopted as the
  standard convention for any future daily-aggregation model --
  documented in `methodology.md` so it isn't rediscovered a third time.
- Found a genuine competitive-intelligence result with zero modeling:
  developer reply strategy differs sharply by app (Paytm blanket-replies
  96% of reviews; Google Pay replies to only 10% but very selectively
  targets 1-star reviews; PhonePe partially targets). Strong README
  headline-finding candidate.
- Identified real spike-day candidates for Phase 6 (Google Pay
  2026-05-18/19 most notably: 2-day sustained elevation + high volume)
  and a genuine regime shift in Paytm's baseline negative share
  starting ~Feb-Mar 2026, flagged for Phase 5's release-impact analysis
  to investigate directly rather than treating it as several unrelated
  spike days.

## 2026-09-18 — Phase 4: topic discovery, codebook v1, and the gold label set

**Topic discovery:** ran BERTopic locally (it installed cleanly on
Windows/Python 3.11 despite the roadmap's Colab fallback plan) on 25,000
reviews with 5+ words. Found 59 real topics + a 26.3% outlier bucket
(typical for short review text). Used this to revise the codebook from
v0 (pre-data draft) to v1: added 3 topics the draft missed
(`autopay_mandates`, `investments_gold`, `travel_booking` -- all
reflecting product features these "UPI apps" have expanded into beyond
payments), confirmed Hinglish/Hindi is central to the corpus (the single
largest cluster, 12.5% of the sample, was Hindi/Hinglish text -- a
stronger finding than Phase 3's rough keyword-marker EDA proxy
suggested), and confirmed `general_praise` as one bucket is correct
despite BERTopic fragmenting it into ~15 clusters (a phrasing artifact,
not distinct sub-topics). Full detail in `config/topics_codebook.md`'s
revision log.

**Gold label set — method decision (user-directed, 2026-09-18):**
presented three options for the 600-review gold set: (1) fully human
hand-labeled by the user (~8-10h, most rigorous), (2) AI-labels
everything, disclosed as such, or (3) hybrid -- AI labels all 600, user
blind-spot-checks a subset. **User chose the hybrid approach.**
Rationale recorded here because it materially affects how the resulting
accuracy numbers should be described in interviews: an AI grading its
own labels is circular and not real validation; a human-labeled subset,
even if smaller than the full 600, gives a genuine independent check.

**Execution:** stratified 600-review sample built via
`src/classify/sample_for_labeling.py` (app x rating-band, 9 strata x 67,
weighted toward longer reviews since Phase 3 found short reviews carry
little topic signal), 150 dev / 450 test split. All 600 labeled directly
against codebook v1 (topics, `churn_intent`, `competitor_mentioned`) in
6 batches of 100, saved to `data/labels/batch_*.json` and merged via
`src/classify/merge_labels.py` into `data/labels/gold_labels.csv`.
Labeler recorded as `ai_v1` in the output -- **not** presented as blind
independent human labels; that check is the separate spot-check below.

**Label distribution (600 reviews, multi-label):** general_praise 46.5%,
app_performance 16.7%, payment_failure 9.2%, customer_support 8.5%,
uninformative 7.8%, rewards_cashback 5.7%, fraud_security 5.0% (more
prevalent than the codebook v1 revision log worried it might be, given
low BERTopic visibility), ui_ux 4.8%, login_otp_kyc/account_blocked 3.0%
each, autopay_mandates/fees_charges 2.3% each, refund_delay 2.0%,
bills_recharge 1.7%, investments_gold 1.5%, bank_linking 1.3%, ads_spam
1.0%, travel_booking 0.8%. churn_intent=true on 2.7% (16/600) --
consistent with the codebook's strict definition (explicit statement of
leaving required, not just a low rating). competitor_mentioned on 2.0%
(12/600) of this stratified sample -- lower than Phase 3's raw regex
scan (3.4-7.9%) because that scan flagged any alias-word occurrence
including false positives, while this is a confirmed, contextual read.

**Human validation (in progress):** built a 120-review blind spot-check
packet (`src/classify/build_spotcheck_packet.py`), sampled specifically
from the **test split** (not dev) since that's what final accuracy
numbers are reported against -- stratified 40/40/40 across the three
apps. Instructions in `data/labels/SPOTCHECK_INSTRUCTIONS.md`,
scoring script at `src/classify/score_spotcheck.py` (computes per-topic
Cohen's kappa, precision/recall/F1, treating the human as ground truth).
**Result pending user completion** -- will update this entry and
`methodology.md` with the real kappa once scored. Until then, any
accuracy number quoted for the classifier should be caveated as
"AI-labeled, human-verified on a 120-review blind subset" rather than
"independently human-validated" outright.

**Known limitation carried into classifier training (Step B):** the
gold set's dev split (150 reviews) is the only human/AI-verified
training data available -- there was no budget/API access to run the
roadmap's original Step A (a separate LLM bulk-labeling pass on ~5,000
reviews) as its own independent process, since I *am* the labeler here
rather than a callable API. This means the embeddings+LogisticRegression
classifier (Step B) will be trained on a much smaller set than the
roadmap envisioned, and rare topics (travel_booking: 5 total examples in
600, ~1 expected in the 150-row dev split) will likely have too little
support for a meaningful per-topic accuracy score. This will be reported
honestly per-topic (flagging "insufficient support" rather than a
misleadingly precise number) rather than papered over with a single
blended accuracy figure.

## 2026-09-18 — Phase 4: classifier trained, rare-topic boost, honest results

**First pass** (trained on the 150-review dev split only): macro-F1
0.392 across the 17 topics with 5+ test examples. Several topics scored
literally 0.0 (`ads_spam`, `investments_gold`) because they had 0-3
training examples in a random 150-row sample -- exactly the risk
flagged when the dev split was built. This is well below the roadmap's
aspirational 0.75 macro-F1 target, which assumed ~5,000 LLM-labeled
training examples (not available here -- see the labeling-method
decision above).

**Fix: keyword-guided rare-topic training boost.** Rather than accept
the weak result or fabricate a larger random sample, built a targeted
224-review training set (`src/classify/sample_rare_topic_boost.py`) by
regex-matching candidate reviews likely to carry each of the 9
lowest-prevalence topics (ads_spam, investments_gold, travel_booking,
autopay_mandates, bank_linking, refund_delay, bills_recharge,
account_blocked, fees_charges) directly from the full corpus --
**explicitly excluding every review_id already in gold_sample.csv**, so
this can never leak into the held-out test split. Labeled all 224
against codebook v1, same process as the main 600. Retrained on
dev(150) + boost(224) = 374 total, re-evaluated on the **same untouched
450-review test set**.

**Result: macro-F1 improved from 0.392 to 0.556** (a 42% relative
gain), micro-F1 0.651 -> 0.686. Every previously-zero topic now scores
non-trivially (ads_spam 0.0->0.353, investments_gold 0.0->0.364,
autopay_mandates 0.125->0.467, account_blocked 0.118->0.462,
bank_linking 0.364->0.667). `general_praise` (the majority class)
remains strongest at F1=0.909. Full per-topic table in
`data/labels/classifier_eval_results.csv`.

**Honest framing for the methodology doc/README:** 0.556 macro-F1 is a
real, defensible number for a classifier trained on 374 examples across
18 multi-label topics -- but it is NOT 0.75+, and should not be
presented as such. `login_otp_kyc` (F1=0.348), `ads_spam` (0.353), and
`investments_gold` (0.364) remain the weakest, meaning topic-share
metrics for these three should be treated as **directional/exploratory**
in later phases (especially Phase 8's RICE backlog), not precise counts.
This is a legitimate engineering trade-off to discuss in interviews:
"I identified a rare-class data shortage through evaluation, fixed it
with targeted keyword-guided sampling rather than brute-force scaling,
and reported the resulting per-topic reliability honestly rather than
hiding behind a single blended metric."

## 2026-09-18 — Phase 4: churn_intent classifier (separate from topics)

Same rare-class problem as the topics: only 8 positive `churn_intent`
examples across dev+rare-topic-boost (374 rows) -- far too thin for a
binary classifier at a real-world ~2-3% base rate. Applied the same
keyword-guided boost technique: 150 candidates matched on explicit
leaving/switching/uninstalling language (`sample_churn_boost.py`),
excluding every review_id already used in gold_sample or
rare_topic_boost_sample so the test split stays uncontaminated. Labeled
all 150 (90 positive, 60% -- confirming the keyword filter worked as a
precision-boosting prior, not just a volume booster). This also forced
a genuine labeling-consistency decision: many matched reviews describe
**uninstall-reinstall as a troubleshooting step** (intending to keep
using the app) rather than **leaving** -- e.g. "uninstalled and
reinstalled, now working" is churn_intent=false, but "uninstalling and
using other apps" is true. Also treated bare imperatives ("uninstall
karo", "delete this app") as ambiguous by default (false) unless the
review's own rating disambiguates (a 1-star review consisting only of
the word "uninstall" is very likely the reviewer's own stated action; a
5-star review saying the same is probably confused/miswritten) --
applied this rule retroactively to 3 early judgment calls for
consistency once the pattern became clear partway through labeling.

**Trained a dedicated binary LogisticRegression** (not folded into the
multi-label topic model) on dev+rare-topic-boost+churn-boost = 524 rows
(98 positive, 18.7%), `class_weight='balanced'`, evaluated on the same
untouched 450-row test split (13 true positives, 2.9% -- realistic
real-world rarity, unlike the enriched training set).
**Result: recall 0.615, precision 0.178, F1 0.276, Cohen's kappa
0.242.** Honest reading: the classifier catches most (8/13) of the
test set's genuine churn statements, but at a real cost in false
positives -- expected and defensible given `class_weight='balanced'`
was chosen to prioritize recall (better to flag a possible at-risk
review for a human/downstream process to check than to silently miss
it), not because the model is highly precise. This number will be
reported as-is in the methodology doc, not rounded up or hidden behind
a single "accuracy" figure (which would look artificially high, ~91%,
purely from the 97%-negative base rate).

## 2026-09-18 — Phase 5: placebo design redesigned; headline result is a validated null

**Placebo design problem found before running anything meaningful:**
the roadmap's plan (placebo dates excluding a ±2x21-day buffer around
every real release) leaves **zero** candidate dates -- PhonePe ships a
new version roughly every 12-16 days over our ~6-month window, denser
than the roadmap assumed for a full year of data. **Fix:** exclude only
the *specific* release under test from its own placebo pool, not every
release. Other real releases can still fall inside some placebo
windows, which makes the null distribution noisier than a truly clean
placebo -- documented as making the significance test **conservative**
(harder to falsely call something significant), not invalid.

**Window-availability check:** of PhonePe's 15 tracked releases, 2 (the
earliest, adopted the same day the data window begins) have zero
pre-period and 1 (the most recent) has only 4 days of post-period --
all 3 excluded as unusable rather than analyzed on a truncated window.
**12 releases usable** with >=7 days on both sides (most have the full
20-21 days).

**Headline result: 0/12 releases significant after Benjamini-Hochberg
correction (q<0.10).** The strongest candidate, `26.05.08.0` (adopted
2026-05-25), stood out sharply from the rest (health score 4.58 vs. the
next-highest 2.12; uncorrected placebo p=0.010) but its q-value (0.122)
just misses the 0.10 threshold.

**Investigated the top candidate rather than stopping at the number,**
using the secondary corroborating method (comparing old vs. new version
ratings on the *same calendar days* during rollout overlap -- controls
for time without needing the competitor-app comparison at all): found
**no corroborating effect** (+0.056 rating difference, p=0.270, wrong
sign for a "worse" release anyway). Investigated further and found why
the two methods disagree: in the DiD comparison window, **both control
apps moved substantially** (Google Pay -5.6pp, Paytm -6.2pp in negative
share) while PhonePe itself was flat (+1.1pp) -- a parallel-trends
violation. Diagnostic chart (`09_diagnostic_parallel_trends.png`) shows
both control apps are highly volatile throughout this whole window (not
a clean before/after step), so this reads as normal noise in two
volatile control series lining up unfavorably for one comparison
window, not a specific dateable incident -- deliberately did not
overstate this as "the Google Pay incident recovering" without
independent confirmation, even though the timing is suggestively close
to the Phase 3 EDA's 2026-05-18/19 Google Pay spike.

**Why this is a valid, useful project finding, not a failed analysis:**
a naive DiD analysis without placebo testing, multiple-testing
correction, AND a corroborating second method would have reported
`26.05.08.0` as a confirmed negative release effect (uncorrected
p=0.01 alone looks compelling) -- a textbook false positive this
pipeline was specifically built to catch. The correct causal
conclusion for this window is: **no PhonePe release shows robust,
validated evidence of a negative causal impact on review sentiment**,
which is itself informative (suggests release-quality stability over
this period) and demonstrates the value of the full validation stack
over a single p-value. Topic-share analysis of the top candidate
(`explain_release.py`) also found a diffuse pre/post shift with no
single dominant driver topic (largest single-topic movement was
`payment_failure` at +0.56pp), consistent with "no real effect" rather
than a specific broken feature.

Outputs: `data/interim/release_impact.csv`, 3 figures
(`07_release_health_scores.png`, `08_placebo_histogram_top_candidate.png`,
`09_diagnostic_parallel_trends.png`), loaded into DuckDB/dbt as
`fct_release_impact` (44/44 dbt checks pass).

## 2026-09-18 — Phase 6: incident log turned out much smaller than planned, and why

**Extensive web research** (WebSearch + WebFetch across ~15 queries,
cross-checked against Wikipedia's "Unified Payments Interface" article
and its own citation list) surfaced many well-documented UPI outages --
but almost all of them (12 April 2025, 26 March 2025, 2 April 2025, 12
May 2025 PhonePe-specific) fall **before** every one of our apps' data
collection windows even starts (Google Pay: 2025-05-04; Paytm:
2025-10-13; PhonePe: 2026-03-18). Well-documented historical incidents
being retrospectively well-covered by press/Wikipedia, while genuinely
recent (2026) incidents are comparatively thin in search results, is
itself a real and somewhat expected asymmetry -- this project collects
data close to real time rather than analyzing a settled historical
period, so the "ground truth" incident record for the exact window we
have reviews for is necessarily less mature than press coverage of
older, more widely-discussed outages.

**Also caught the search tool's natural-language summaries misattributing
dates** on at least two occasions (a 12 May 2025 PhonePe-specific outage
summarized as "February 2026"; an April 2025 NPCI statement summarized
as attached to "August 14, 2026") -- caught by independently checking
the Business Standard URL's embedded `YYMMDD` numeric ID pattern and by
fetching the underlying Wikipedia citation list directly via the API
rather than trusting the fetch tool's own summarization. Lesson: verify
specific dates against a primary source or a structured citation list,
never take a search summary's date at face value for anything that
becomes a hard-coded ground-truth entry.

**Also tried to independently confirm the Phase 3 EDA's own candidate
signal** (Google Pay's 2026-05-18/19 negative-share spike) as a
reported news event -- found no corroborating coverage. This is an
honest, useful negative result on its own: the spike may be a real but
smaller/regional issue below the threshold of national tech press
coverage (arguably a point in favor of review-based monitoring, which
could surface user-facing problems press coverage doesn't), or it may
be unrelated noise -- reported as an **unconfirmed candidate signal**,
not a validated incident, and clearly labeled as such wherever it's
used.

**Result: exactly ONE incident meets the bar** (independently
multi-sourced AND falls within a reviewable app's data window):
**2025-08-07, ~19:45 IST**, a UPI-wide outage (Google Pay, PhonePe,
Paytm all affected per reporting; NPCI attributed it to bank-side
technical issues at HDFC/SBI/Bank of Baroda/Kotak Mahindra). Cross-
verified via Wikipedia's own citation list (Economic Times x2,
Hindustan Times, Financial Express -- 4 independent sources). Usable
**only against Google Pay's review data** -- it predates Paytm's and
PhonePe's collection windows entirely.

**Design pivot for the rest of Phase 6, made explicit rather than
silently working around a thin ground truth:**
1. With n=1 confirmed incident, a recall/precision percentage would be
   statistically meaningless (0% or 100%, no in-between) -- Phase 6
   reports this as a **single validated case study**, not a powered
   evaluation, and says so plainly rather than dressing up n=1 as a
   real recall rate.
2. Still measure **false-alert rate** over many quiet (non-incident)
   periods -- that part of the evaluation doesn't need a large
   incident count and remains statistically meaningful.
3. Report the detector's behavior around the Phase 3 candidate signal
   (2026-05-18/19) as a secondary, clearly-labeled **unconfirmed
   candidate detection** -- a demonstration of the system surfacing
   something real-looking in the data even without press confirmation,
   not claimed as a second validated incident.
4. This changes Phase 6's contribution from "we measured X% recall"
   to "we built and stress-tested a working detector, validated it
   against the one incident we could independently confirm falls in
   our window, and characterized its false-alert behavior on quiet
   periods" -- a more honest and, arguably, more interesting story
   about the real difficulty of ground-truthing a live monitoring
   system, which is itself worth discussing in interviews.

## 2026-09-19 — Phase 7: true competitor-mention rate is much lower than Phase 3's estimate

**Found and explained a measurement error from Phase 3's EDA** (the
"do we have enough data" competitor-mention check, 2026-09-18): that
scan reported 3.4-7.9% of reviews per app "mention a competitor",
which fed directly into the "yes, we have enough data" conclusion for
Phase 7. Re-running the extraction properly for Phase 7 (excluding
mentions of the REVIEWING app's own name, using the full
`config/aliases.yaml` variant list per app) finds the true rate is
**0.54%** (1,578 of 291,197 reviews) -- an order of magnitude lower.
Root cause: the Phase 3 scan's regex matched any of the 3 main apps'
names without excluding self-mentions, so a PhonePe review saying
"phonepe" (extremely common -- users name the app they're reviewing
constantly) inflated PhonePe's own "competitor mention" count. The
correct metric for a switching analysis only cares about a review
mentioning a **different** app than the one being reviewed.

**Still workable, but with real limits on precision per cell:** 1,578
candidates split across app pairs and relation types means some
specific (source, destination) cells in the eventual switching matrix
will have thin support. Handled the same way Phase 4 handled sparse
classes: report bootstrap confidence intervals rather than point
estimates alone, and flag low-support cells explicitly rather than
implying false precision.

Mention counts by app being reviewed: Google Pay 620, Paytm 510,
PhonePe 448. Most-mentioned other apps: Google Pay 576, PhonePe 467,
Paytm 319, BHIM 266, Supermoney 95, Amazon Pay 69, CRED 41, Navi 39,
WhatsApp Pay 2 (too thin to use).

## 2026-09-19 — Phase 7: relation classifier validated and improved

**Method choice:** rule-based regex classifier for the
switching_away / switched_from_competitor / comparison_only / none
relation between a review and the other app(s) it mentions, rather
than another full ML pipeline -- consistent with this session's
established pattern of matching method complexity to task size (1,578
candidates doesn't justify a full embeddings+classifier build the way
the 291K-review topic corpus did).

**Manually validated a 183-review stratified sample** (60
switching_away, 60 comparison_only, 60 none, all 3
switched_from_competitor) against the classifier's predictions.
Findings:
- **Precision on positive predictions was good** (roughly 85-90% for
  switching_away, ~95% for comparison_only, 3/3 correct for the tiny
  switched_from_competitor class) -- when the classifier says there's a
  relation, it's usually right.
- **Recall had real, identifiable gaps**: roughly 40-50% of the
  sampled "none" predictions were, on inspection, true comparisons or
  switching statements the regex missed -- common causes: phrasing
  variants not in the pattern list ("using X" without explicit "I am",
  "switched to/in X" past tense, "going for X", "compare with X" vs
  "compared to X"), adverbs breaking rigid word-adjacency
  ("is **actually** faster than" not matching an "is faster" pattern
  expecting immediate adjacency), and word-order variants ("instead
  use X" vs "use X instead"). **Hindi/Hinglish comparisons were missed
  entirely** by the English-only patterns -- a real scope limitation,
  not something a few more regex lines fixes properly.

**Fixed the cheap, well-justified gaps** (past-tense "switched to X",
"going for X", "using X", relaxed word-adjacency in comparison
patterns, a handful of common Hinglish comparative constructions
actually observed in the sample, NOT full Hindi coverage) and
re-ran: comparison_only 358->466, switching_away 115->157, none
1398->1248. Spot-checked 20 of the originally-identified misses after
the fix -- about half are now caught; the rest need increasingly
specific patterns for diminishing returns (typos like "rathern than",
unusual phrasing like "switched in paytm", plural subjects), a
reasonable stopping point for a rule-based approach.

**Headline honesty for the switching map:** these counts are a
**lower bound** on true switching signal, not a precise count -- the
regex is more conservative (higher precision, imperfect recall) than
an LLM classifier would likely be. Stated explicitly in the
methodology doc rather than presented as exhaustive.

## 2026-09-19 — Phase 8: two interpretive caveats caught before finalizing the backlog

**`ui_ux` has a positive rating-penalty coefficient (+0.375, highly
significant)** -- the only topic where this happens. Rather than
silently including it in the automated RICE ranking (where it lands in
the top 5 for 2 of 3 apps because `rating_lift_if_fixed` uses
`abs(penalty)`), investigated why: `ui_ux` was frequently co-tagged
with `general_praise` during Phase 4 labeling (constructive feature
requests from otherwise-happy reviewers -- "great app, please add X" --
not pure UI complaints). The topic tag conflates two different reviewer
populations, so a rating "penalty" framing doesn't apply cleanly. **Fix:
flag `ui_ux` explicitly in the backlog output as needing manual
interpretation rather than trusting the automated score** -- the RICE
math still runs (for consistency/completeness), but the PM brief
excludes it from the auto-prioritized top list and explains why.

**Reach uses Play Store download counts** (PhonePe/Paytm 500M+, Google
Pay 1B+ -- verified Phase 0), not true MAU, because third-party "MAU"
statistics found via search were inconsistent across sources (some
from content-mill sites, not primary reporting) and not trustworthy
enough to hard-code into an analysis. This is a real limitation stated
explicitly: download count overstates true active reach, and because
Google Pay's download count is 2x PhonePe/Paytm's, its RICE scores are
higher almost everywhere **partly as an artifact of that scale
difference**, not necessarily because its issues are twice as severe.
**Within-app ranking (which topic to fix first for a GIVEN app) is the
methodologically sound use of this table; cross-app RICE comparison is
not**, and the backlog write-up says so rather than implying "fix
Google Pay's issues before PhonePe's" from the raw numbers.

**Robust finding that holds regardless of both caveats:**
`app_performance` is the #1 RICE-ranked issue for all 3 apps
independently -- consistent across apps with different reach scales and
unaffected by the ui_ux issue, a genuinely convergent result worth
leading with.

## 2026-09-19 — Phase 9: a real tooling limitation, disclosed rather than worked around

**Cannot actually assemble the `.pbix` file.** Power BI Desktop's
report-building surface (dragging visuals onto a canvas, wiring up
fields) is GUI-only with no CLI/scripting interface, and this session
has no GUI-automation tool for arbitrary Windows desktop apps (only web
browser tooling). Rather than skip Power BI entirely or pretend to
produce a `.pbix` that wasn't actually built, did everything that IS
buildable programmatically -- the full star schema in dbt (`dim_date`,
`dim_app`, `dim_topic`, `dim_version`, plus the 6 fact marts already
built in Phases 3-8), all 11 tables exported to CSV
(`data/exports/`), every relationship and DAX measure fully specified,
and a page-by-page build spec -- in
`dashboards/POWERBI_BUILD_GUIDE.md`, written so the remaining GUI
assembly step is a mechanical follow-along, not a design task.

**One modeling simplification worth remembering:** `dim_version`
already has the Phase 5 release-impact fields (`real_effect`,
`q_value`, `is_significant`) joined in via a left join to
`fct_release_impact` in the dbt model itself -- so the Power BI model
should relate to `dim_version` directly for the Release Impact page
rather than ALSO relating `fct_release_impact` (that table is exported
mainly for direct SQL/Python reference, not intended as a second
Power BI relationship to the same conceptual data).

**`fct_switching`'s double relationship to `dim_app`** (source and
dest) needs `USERELATIONSHIP()` in DAX for the inactive direction --
documented explicitly in the build guide with a worked `[Inflow Count]`
example, since this is a common Power BI modeling gotcha that produces
silently wrong numbers if missed (the inactive relationship just
returns 0/blank instead of erroring).

## 2026-09-19 — Phase 10: storytelling and packaging, project complete

Wrote the recruiter-facing `README.md` (TL;DR, architecture diagram as
Mermaid rather than an unsavable screenshot -- this session has no
OS-level screenshot tool, only browser-page tooling, so a hand-written
Mermaid diagram that GitHub renders natively is both more reliable and
matches the roadmap's own Phase 10 example), 3 PM briefs with real
numbers pulled directly from the warehouse (`reports/briefs/`), and
`reports/RESUME_BULLETS.md` with role-targeted variants.

**Went back through `project_charter.md`'s original Success Criteria
and reported actual results rather than quietly dropping unmet ones:**
the 0.75 macro-F1 target was not met (0.556 actual — the target assumed
~5,000 LLM-labeled examples this project never had budget for); the
"70% recall" early-warning target turned out not evaluable at all given
only 1 confirmed incident (not the 15-25 originally planned); the
placebo-p-value and PM-brief/methodology/README deliverable targets
were met. Recording the misses alongside the hits is the same
principle this whole project has followed since Phase 1 -- a
resume/interview story built on selectively reported success criteria
would be exactly the kind of thing a careful interviewer catches.

**Two items intentionally left for the user, not faked:** the
120-review blind spot-check (independent human validation of the topic
classifier) and the Power BI `.pbix` GUI assembly step. Both are fully
prepared (packet + scoring script; full build guide) with clear
instructions, rather than skipped silently or their results invented.

This closes all 10 phases of `ROADMAP.md`.

## (Template for future entries)

**Decision:** ...
**Why:** ...
**Alternatives considered:** ...
**Result / what I'd check next:** ...

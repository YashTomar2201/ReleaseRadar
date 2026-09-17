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

## (Template for future entries)

**Decision:** ...
**Why:** ...
**Alternatives considered:** ...
**Result / what I'd check next:** ...

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

## (Template for future entries)

**Decision:** ...
**Why:** ...
**Alternatives considered:** ...
**Result / what I'd check next:** ...

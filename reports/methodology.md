# ReleaseRadar — Methodology

> Built incrementally as each phase completes. This is the document a
> skeptical interviewer's questions get answered from — see
> `decision_log.md` for the full reasoning trail behind each choice.

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

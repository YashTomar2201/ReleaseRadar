-- The Play Store gives no public version-history API. We infer each
-- version's "adoption date" from the reviews themselves: the first day
-- a version makes up at least 5% of that app's daily reviews. The 5%
-- threshold filters out stray early/beta-channel reviewers so we don't
-- mistake a handful of early adopters for the real rollout date.
--
-- Validated in decision_log.md (Phase 2, 2026-09-18): PhonePe is not
-- listed on APKMirror (the roadmap's original validation plan), so
-- instead we cross-checked against PhonePe's own version-string-encoded
-- build date (YY.MM.DD.build) -- all 15 inferred releases show a tight
-- 13-33 day gap (median 17) between build and adoption, matching a
-- staged-rollout pattern.

with max_complete_date as (
    -- Phase 1 found a ~24-25h (median 31-34h) review-indexing lag in the
    -- Play Store API, so the most recent ~2 days per app have
    -- incomplete counts. Left in, a trailing version can spuriously
    -- cross the 5% share threshold simply because that day's total is
    -- still small -- confirmed in the decision log (2026-09-18):
    -- version 25.10.03.0 got a bogus adoption_date 349 days after its
    -- build-date-encoded version string, driven entirely by this edge
    -- effect on the last available day.
    select app_key, max(review_date) - interval 2 day as cutoff_date
    from {{ ref('stg_reviews') }}
    group by 1
),

daily_version as (
    select r.app_key, r.review_date, r.review_version, count(*) as n
    from {{ ref('stg_reviews') }} r
    join max_complete_date c on r.app_key = c.app_key
    where r.review_version is not null
      and r.review_date <= c.cutoff_date
    group by 1, 2, 3
),

with_share as (
    select
        *,
        n * 1.0 / sum(n) over (partition by app_key, review_date) as version_share
    from daily_version
),

first_adopted as (
    select
        app_key,
        review_version,
        min(review_date) filter (where version_share >= 0.05) as adoption_date,
        min(review_date)                                      as first_seen_date,
        sum(n)                                                as total_reviews
    from with_share
    group by 1, 2
)

select *
from first_adopted
where adoption_date is not null
  and total_reviews >= 200  -- enough reviews to support a release-impact analysis
order by app_key, adoption_date

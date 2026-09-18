-- is_complete_day: Phase 1 found a ~24-25h (median 31-34h) review-
-- indexing lag in the Play Store API, so the most recent ~2 days per
-- app have sharply undercounted reviews (confirmed in Phase 3 EDA: the
-- last day's n_reviews drops from a normal 170-650/day to 10-19,
-- producing a wildly noisy negative_share purely from small-sample
-- variance -- e.g. PhonePe's last day showed 42% negative from just 19
-- reviews). This is the same root cause already fixed in
-- int_version_adoption (Phase 2); flagging it here rather than
-- silently dropping rows, so consumers can filter with
-- `where is_complete_day` while the raw counts stay inspectable.
-- Any future daily-aggregation model should follow the same pattern.

select
    app_key,
    review_date,
    count(*)                                       as n_reviews,
    avg(rating)                                    as avg_rating,
    avg(case when is_negative then 1.0 else 0 end) as negative_share,
    avg(avg(rating)) over (
        partition by app_key order by review_date
        rows between 6 preceding and current row
    )                                              as avg_rating_7d,
    review_date <= (
        max(review_date) over (partition by app_key) - interval 2 day
    )                                              as is_complete_day
from {{ ref('stg_reviews') }}
group by 1, 2
order by 1, 2

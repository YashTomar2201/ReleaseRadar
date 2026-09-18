-- Daily topic volume per app. Follows the is_complete_day convention
-- established in fct_daily_app_metrics (Phase 3, decision_log.md
-- 2026-09-18) -- every daily-aggregation model in this project excludes
-- the trailing 2 days per app from being treated as complete, since the
-- Play Store's ~24-25h review-indexing lag (Phase 1) undercounts them.

select
    t.app_key,
    t.review_date,
    t.topic,
    count(distinct t.review_id)                                   as n_topic_reviews,
    d.n_reviews                                                    as n_reviews_that_day,
    round(count(distinct t.review_id) * 1.0 / nullif(d.n_reviews, 0), 4) as topic_share,
    d.is_complete_day
from {{ ref('stg_review_topics') }} t
join {{ ref('fct_daily_app_metrics') }} d
    on t.app_key = d.app_key and t.review_date = d.review_date
group by 1, 2, 3, 5, 7
order by 1, 2, 3

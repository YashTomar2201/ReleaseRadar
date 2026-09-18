-- ReleaseRadar — reference SQL queries (DuckDB dialect)
-- Run against data/warehouse/releaseradar.duckdb. These demonstrate
-- window functions, CTEs, QUALIFY, and percentile logic beyond what
-- the dbt marts already compute -- ad hoc analyst-style queries, not
-- part of the pipeline itself.

-- =====================================================================
-- 1. Top 3 topics by week-over-week share increase, per app
-- =====================================================================
with weekly as (
    select app_key, topic, date_trunc('week', review_date) as wk,
           sum(n_topic_reviews) as n
    from main.fct_daily_topic_metrics
    where is_complete_day
    group by 1, 2, 3
),
totals as (
    select app_key, date_trunc('week', review_date) as wk, sum(n_reviews) as total
    from main.fct_daily_app_metrics
    where is_complete_day
    group by 1, 2
),
shares as (
    select w.*, w.n * 1.0 / t.total as share,
           lag(w.n * 1.0 / t.total) over (partition by w.app_key, w.topic order by w.wk) as prev_share
    from weekly w join totals t using (app_key, wk)
)
select app_key, wk, topic, round(share, 4) as share, round(share - prev_share, 4) as wow_change
from shares
where wk = (select max(wk) from shares)
qualify row_number() over (partition by app_key order by share - prev_share desc) <= 3;


-- =====================================================================
-- 2. Rolling 7-day average rating per app, with day-over-day delta
-- =====================================================================
select
    app_key,
    review_date,
    avg_rating,
    avg_rating_7d,
    round(avg_rating - lag(avg_rating) over (partition by app_key order by review_date), 3) as day_over_day_delta
from main.fct_daily_app_metrics
where is_complete_day
order by app_key, review_date;


-- =====================================================================
-- 3. Median and P90 review length by app (percentile logic)
-- =====================================================================
select
    app_key,
    median(text_length) as median_len,
    quantile_cont(text_length, 0.90) as p90_len,
    quantile_cont(text_length, 0.99) as p99_len
from main.stg_reviews
group by 1;


-- =====================================================================
-- 4. Cohort-style: rating trajectory of reviewers by their FIRST topic
--    (which issue "acquired" the complaint, and how does sentiment
--    move afterward within the same app-month)
-- =====================================================================
with first_topic as (
    select review_id, app_key, topic, review_date,
           row_number() over (partition by review_id order by review_date) as rn
    from main.stg_review_topics
    qualify rn = 1
)
select
    ft.app_key,
    ft.topic as first_topic,
    strftime(ft.review_date, '%Y-%m') as cohort_month,
    count(distinct ft.review_id) as n_reviewers,
    round(avg(r.rating), 2) as avg_rating
from first_topic ft
join main.stg_reviews r on ft.review_id = r.review_id
group by 1, 2, 3
order by 1, 3, 4 desc;


-- =====================================================================
-- 5. Which topics most often co-occur with app_performance? (a review
--    can carry multiple topics -- this finds the strongest pairings)
-- =====================================================================
with app_perf_reviews as (
    select review_id, app_key from main.stg_review_topics where topic = 'app_performance'
)
select
    t.topic as co_occurring_topic,
    count(*) as n_co_occurrences,
    round(100.0 * count(*) / (select count(*) from app_perf_reviews), 2) as pct_of_app_performance_reviews
from main.stg_review_topics t
join app_perf_reviews a on t.review_id = a.review_id
where t.topic != 'app_performance'
group by 1
order by 2 desc;


-- =====================================================================
-- 6. Release-impact leaderboard: all 15 tracked PhonePe releases,
--    ranked by |health_score|, with usability/significance flags
--    (mirrors fct_release_impact but shown as a readable leaderboard)
-- =====================================================================
select
    version,
    adoption_date,
    round(real_effect, 4) as real_effect,
    round(health_score, 2) as health_score,
    round(q_value, 3) as q_value,
    is_significant,
    usable,
    rank() over (order by abs(health_score) desc) as rank_by_abs_health_score
from main.fct_release_impact
order by rank_by_abs_health_score;

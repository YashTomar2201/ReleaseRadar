-- Anonymized example reviews for drill-through (Topic Explorer page).
-- Up to 8 reviews per (app, topic, month), prioritizing negative
-- reviews first since those carry the most actionable context, with
-- some positive/neutral mixed in for balance. Never load the full
-- 291K-review corpus into Power BI -- this bounded sample is the
-- intended drill-through source instead.
with ranked as (
    select
        t.app_key,
        t.topic,
        strftime(t.review_date, '%Y-%m') as year_month,
        r.review_id,
        r.rating,
        r.review_text,
        r.review_date,
        row_number() over (
            partition by t.app_key, t.topic, strftime(t.review_date, '%Y-%m')
            order by r.rating asc, random()
        ) as rn
    from {{ ref('stg_review_topics') }} t
    join {{ ref('stg_reviews') }} r on t.review_id = r.review_id
)
select app_key, topic, year_month, review_id, rating, review_text, review_date
from ranked
where rn <= 8

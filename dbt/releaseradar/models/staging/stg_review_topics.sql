-- One row per (review, topic) the Phase 4 classifier predicted
-- positive. Joined to stg_reviews so downstream models get app_key/
-- review_date without a second join every time.
select
    t.review_id,
    r.app_key,
    r.review_date,
    r.review_hour,
    t.topic,
    t.probability
from {{ source('raw', 'review_topics') }} t
join {{ ref('stg_reviews') }} r on t.review_id = r.review_id

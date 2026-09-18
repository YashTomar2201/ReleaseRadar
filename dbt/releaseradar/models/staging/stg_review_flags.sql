-- One row per review with the churn_intent prediction. See
-- _sources.yml for the classifier's precision/recall -- tuned to favor
-- recall, so treat churn_intent=true as "worth a closer look", not
-- a confirmed signal on its own.
select
    f.review_id,
    r.app_key,
    r.review_date,
    f.churn_intent,
    f.churn_probability
from {{ source('raw', 'review_flags') }} f
join {{ ref('stg_reviews') }} r on f.review_id = r.review_id

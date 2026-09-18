-- Singular test: avg_rating must fall within the Play Store's 1-5 scale.
select *
from {{ ref('fct_daily_app_metrics') }}
where avg_rating < 1 or avg_rating > 5

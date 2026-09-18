-- Calendar dimension spanning the full data range across all apps.
select
    d::date                         as date,
    extract(year from d)            as year,
    extract(month from d)           as month,
    strftime(d, '%Y-%m')            as year_month,
    extract(dow from d)             as day_of_week,
    extract(dow from d) in (0, 6)   as is_weekend
from generate_series(
    (select min(review_date) from {{ ref('stg_reviews') }}),
    (select max(review_date) from {{ ref('stg_reviews') }}),
    interval 1 day
) as t(d)

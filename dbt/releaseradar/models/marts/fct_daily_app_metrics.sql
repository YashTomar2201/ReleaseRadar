select
    app_key,
    review_date,
    count(*)                                       as n_reviews,
    avg(rating)                                    as avg_rating,
    avg(case when is_negative then 1.0 else 0 end) as negative_share,
    avg(avg(rating)) over (
        partition by app_key order by review_date
        rows between 6 preceding and current row
    )                                              as avg_rating_7d
from {{ ref('stg_reviews') }}
group by 1, 2
order by 1, 2

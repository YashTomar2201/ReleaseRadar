select
    app_key,
    version,
    cast(adoption_date as date) as adoption_date,
    n_pre_days,
    n_post_days,
    usable,
    real_effect,
    n_placebo,
    placebo_p,
    q_value,
    health_score,
    is_significant
from {{ source('raw', 'release_impact') }}

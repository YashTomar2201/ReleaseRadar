select
    source,
    dest,
    n,
    source_total_reviews,
    per_10k,
    per_10k_ci_low,
    per_10k_ci_high
from {{ source('raw', 'switching_matrix') }}

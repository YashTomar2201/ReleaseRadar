-- Release/version dimension, joined to the Phase 5 impact results
-- where available (PhonePe only -- the only app with a release-impact
-- analysis; see fct_release_impact for why 0/12 are significant).
select
    v.app_key,
    v.review_version,
    v.adoption_date,
    v.total_reviews,
    r.usable as impact_analysis_usable,
    r.real_effect,
    r.q_value,
    r.is_significant
from {{ ref('int_version_adoption') }} v
left join {{ ref('fct_release_impact') }} r
    on v.app_key = r.app_key and v.review_version = r.version

-- One row per tracked PhonePe release with its DiD effect and
-- placebo-test validation. See stg_release_impact / _sources.yml for
-- the headline result: 0/12 usable releases are significant after
-- multiple-testing correction in this ~6-month window.
select * from {{ ref('stg_release_impact') }}
order by adoption_date

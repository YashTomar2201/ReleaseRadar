-- Singular test: negative_share is a proportion and must stay in [0, 1].
-- dbt convention: a singular test PASSES when it returns ZERO rows, so
-- we select the rows that VIOLATE the rule.
select *
from {{ ref('fct_daily_app_metrics') }}
where negative_share < 0 or negative_share > 1

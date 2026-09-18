-- One row per detected alert episode. See decision_log.md (2026-09-18)
-- for why this is validated against a single confirmed incident
-- (INC001, Google Pay 2025-08-07) rather than a statistically powered
-- recall estimate, plus a false-alert-rate characterization per app.
select * from {{ ref('stg_alerts') }}
order by app_key, alert_start

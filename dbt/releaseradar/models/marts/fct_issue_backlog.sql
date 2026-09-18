-- One row per (app, topic) with the full RICE breakdown. See
-- decision_log.md, 2026-09-19: app_performance is the #1 RICE-ranked
-- issue for all 3 apps independently and is stable under effort
-- uncertainty (99-100% top-3 stability); ui_ux needs manual review
-- (positive rating coefficient -- co-occurs with praise); reach is a
-- download-count proxy valid for within-app ranking only.
select * from {{ ref('stg_issue_backlog') }}
order by app_key, rice desc

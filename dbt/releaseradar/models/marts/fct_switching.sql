-- One row per (source, dest) switching flow. Counts are a LOWER BOUND
-- on true switching signal (rule-based relation classifier has good
-- precision but imperfect recall -- see decision_log.md, 2026-09-19).
select * from {{ ref('stg_switching_matrix') }}
order by n desc

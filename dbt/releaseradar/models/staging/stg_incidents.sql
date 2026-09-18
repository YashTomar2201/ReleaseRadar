select
    incident_id,
    apps_affected,
    cast(start_time_ist as timestamp) as start_time_ist,
    cast(first_public_report_ist as timestamp) as first_public_report_ist,
    type,
    notes
from {{ source('raw', 'incidents') }}

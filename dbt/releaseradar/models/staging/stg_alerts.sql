select
    app_key,
    cast(start as timestamp) as alert_start,
    cast("end" as timestamp) as alert_end,
    peak_p
from {{ source('raw', 'alerts') }}

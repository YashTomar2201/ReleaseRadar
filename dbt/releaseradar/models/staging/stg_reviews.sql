with source as (
    select * from {{ source('raw', 'reviews') }}
),

deduped as (
    -- Reviews can appear more than once across weekly re-scrapes (same
    -- reviewId reappears if it's still within the Play Store's newest-N
    -- pagination window). Keep only the most recently scraped copy --
    -- it may carry an updated thumbsUpCount or a dev reply added since.
    select
        *,
        row_number() over (partition by "reviewId" order by scraped_at desc) as rn
    from source
)

select
    "reviewId"                       as review_id,
    app_key,
    user_hash,
    trim(content)                    as review_text,
    cast(score as integer)           as rating,
    "thumbsUpCount"                  as thumbs_up,
    "reviewCreatedVersion"           as review_version,
    "at"                             as reviewed_at,
    cast("at" as date)               as review_date,
    date_trunc('hour', "at")         as review_hour,
    "replyContent" is not null       as has_dev_reply,
    length(trim(content))            as text_length,
    cast(score as integer) <= 2      as is_negative,
    scraped_at
from deduped
where rn = 1
  and content is not null
  and length(trim(content)) > 0

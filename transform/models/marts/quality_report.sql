-- How much data each cleaning rule caught. A reading can break more than one rule.

with daily as (
    select
        'daily' as level,
        count(*) as readings,
        count(*) filter (where flag_impossible) as impossible,
        count(*) filter (where flag_incomplete) as incomplete,
        count(*) filter (where flag_flat) as flat_or_stuck,
        count(*) filter (where flag_repeated) as repeated,
        count(*) filter (where flag_city_outlier) as outlier_or_spike,
        count(*) filter (
            where flag_impossible or flag_incomplete or flag_flat or flag_repeated or flag_city_outlier
        ) as any_rule
    from {{ ref('int_air_daily_flagged') }}
),

hourly as (
    select
        'hourly' as level,
        count(*),
        count(*) filter (where flag_impossible),
        count(*) filter (where flag_incomplete),
        count(*) filter (where flag_stuck),
        0,
        count(*) filter (where flag_spike),
        count(*) filter (where flag_impossible or flag_incomplete or flag_stuck or flag_spike)
    from {{ ref('int_air_hourly_flagged') }}
)

select *, round(100.0 * any_rule / readings, 1) as pct_removed
from (select * from daily union all select * from hourly)

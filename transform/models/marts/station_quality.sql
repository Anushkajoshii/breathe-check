-- Per-station share of usable days. Useful to spot stations that are mostly broken.
select
    f.city,
    f.location_id,
    any_value(s.name) as station_name,
    min(f.date) as first_day,
    max(f.date) as last_day,
    count(*) as days_reported,
    count(*) filter (
        where not (flag_impossible or flag_incomplete or flag_flat or flag_repeated or flag_city_outlier)
    ) as days_usable,
    round(100.0 * days_usable / days_reported, 1) as pct_usable
from {{ ref('int_air_daily_flagged') }} f
left join {{ ref('stg_stations') }} s using (location_id)
group by all

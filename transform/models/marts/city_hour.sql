-- One row per city per hour (Feb 2025 onwards): PM2.5 over clean stations, plus weather.
-- This feeds the "safest hours to run" forecast.

with clean as (
    select * from {{ ref('int_air_hourly_flagged') }}
    where not (flag_impossible or flag_incomplete or flag_stuck or flag_spike)
),

air as (
    select city, time_ist, avg(pm25) as pm25, count(*) as n_stations
    from clean
    group by all
)

select
    a.city,
    a.time_ist,
    hour(a.time_ist) as hour,
    a.pm25,
    a.n_stations,
    w.* exclude (city, time_ist)
from air a
-- Air hours start on :00 India time, weather is measured on :30 (whole UTC hours),
-- so each air hour gets the weather reading from its middle.
left join {{ ref('stg_weather') }} w
    on w.city = a.city and w.time_ist = a.time_ist + interval 30 minute

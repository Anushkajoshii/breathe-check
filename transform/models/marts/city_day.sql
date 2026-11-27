/*
The main analysis table: one row per city per day, with:
  - PM2.5 averaged over the city's clean stations that day
  - the day's weather
  - the GRAP stage in force (Delhi-NCR only; 0 elsewhere)
  - whether the original GRAP season was on, days from Diwali, and crop fires
*/

with clean as (
    select * from {{ ref('int_air_daily_flagged') }}
    where not (flag_impossible or flag_incomplete or flag_flat or flag_repeated or flag_city_outlier)
),

air as (
    select
        city,
        date,
        avg(pm25) as pm25,
        median(pm25) as pm25_median,
        count(*) as n_stations
    from clean
    group by all
),

weather as (
    select
        city,
        cast(time_ist as date) as date,
        avg(temp_c) as temp_c,
        min(temp_c) as temp_min_c,
        max(temp_c) as temp_max_c,
        avg(humidity_pct) as humidity_pct,
        avg(dew_point_c) as dew_point_c,
        sum(rain_mm) as rain_mm,
        avg(pressure_hpa) as pressure_hpa,
        avg(cloud_pct) as cloud_pct,
        avg(wind_kmh) as wind_kmh,
        max(gust_kmh) as gust_max_kmh,
        avg(mixing_height_m) as mixing_height_m,
        min(mixing_height_m) as mixing_height_min_m,
        sum(sun_wm2) / 1000 as sun_kwh_m2,
        -- average wind as a direction: break each hour into east/north parts first
        avg(-wind_kmh * sin(radians(wind_dir_deg))) as wind_u,
        avg(-wind_kmh * cos(radians(wind_dir_deg))) as wind_v,
        count(*) as weather_hours
    from {{ ref('stg_weather') }}
    group by all
),

fires as (
    select
        date,
        count(*) as fires,
        count(*) filter (where confidence <> 'l') as fires_confident,
        sum(fire_power_mw) as fire_power_mw
    from {{ ref('stg_fires') }}
    group by all
),

calendar as (
    select
        c.slug as city,
        c.role as city_role,
        d.date
    from {{ ref('stg_cities') }} c
    cross join (select distinct date from air) d
)

select
    k.city,
    k.city_role,
    k.date,
    year(k.date) as year,
    month(k.date) as month,
    dayofweek(k.date) as weekday,  -- 0 = Sunday
    a.pm25,
    a.pm25_median,
    coalesce(a.n_stations, 0) as n_stations,
    w.* exclude (city, date),
    -- wind direction the air is coming from, in degrees (0 = north, 270 = west)
    (degrees(atan2(-w.wind_u, -w.wind_v)) + 360) % 360 as wind_from_deg,
    case when k.city_role = 'grap' then coalesce(g.grap_stage, 0) else 0 end as grap_stage,
    case when k.city_role = 'grap' then coalesce(g.grap_stage_sure_only, 0) else 0 end
        as grap_stage_sure_only,
    exists (
        select 1 from {{ ref('stg_grap_original') }} s
        where k.date between s.season_start and s.season_end
    ) and k.city_role = 'grap' as original_grap_season,
    k.date - dw.diwali_date as days_from_diwali,
    coalesce(f.fires, 0) as fires,
    coalesce(f.fires_confident, 0) as fires_confident,
    coalesce(f.fire_power_mw, 0) as fire_power_mw,
    coalesce(f1.fires_confident, 0) as fires_confident_yesterday
from calendar k
left join air a using (city, date)
left join weather w using (city, date)
left join {{ ref('stg_grap_daily') }} g on g.date = k.date
left join {{ ref('stg_diwali') }} dw on dw.year = year(k.date)
left join fires f on f.date = k.date
left join fires f1 on f1.date = k.date - 1

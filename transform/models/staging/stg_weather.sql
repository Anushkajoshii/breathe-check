-- Hourly weather per city: the archive, topped up with the recent forecast file
-- for days the archive does not have yet.
with archive as (
    select *, 'archive' as weather_source
    from read_parquet('{{ var("raw_dir") }}/weather/*/*.parquet')
    -- the archive returns empty rows for the last few days; skip those
    where temperature_2m is not null
),

recent as (
    select *, 'forecast' as weather_source
    from read_parquet('{{ var("raw_dir") }}/weather_forecast/*/*.parquet')
    where (city, time_utc) not in (select city, time_utc from archive)
),

both_sources as (
    select * from archive
    union all by name
    select * from recent
)

select
    city,
    {{ to_ist('time_utc') }} as time_ist,
    temperature_2m as temp_c,
    relative_humidity_2m as humidity_pct,
    dew_point_2m as dew_point_c,
    precipitation as rain_mm,
    surface_pressure as pressure_hpa,
    cloud_cover as cloud_pct,
    wind_speed_10m as wind_kmh,
    wind_direction_10m as wind_dir_deg,
    wind_gusts_10m as gust_kmh,
    boundary_layer_height as mixing_height_m,
    shortwave_radiation as sun_wm2,
    weather_source
from both_sources

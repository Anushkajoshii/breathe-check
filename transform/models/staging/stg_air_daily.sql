-- Daily PM2.5 per station, as it came from OpenAQ. One row per station per day.
select
    city,
    location_id,
    sensor_id,
    cast(substr(start_local, 1, 10) as date) as date,  -- the India-time day
    value as pm25,
    "min" as pm25_min,
    "max" as pm25_max,
    sd as pm25_sd,
    percent_complete,
    has_flags as openaq_flagged
from read_parquet('{{ var("raw_dir") }}/air_daily/*/*.parquet')

-- Hourly PM2.5 per station. time_ist is the start of the hour in India time.
select
    city,
    location_id,
    sensor_id,
    {{ to_ist('start_utc') }} as time_ist,
    value as pm25,
    percent_complete,
    has_flags as openaq_flagged
from read_parquet('{{ var("raw_dir") }}/air_hourly/*/*.parquet')

-- One row per satellite fire detection in Punjab and Haryana.
select
    region,
    cast({{ to_ist('time_utc') }} as date) as date,
    latitude,
    longitude,
    frp as fire_power_mw,
    confidence,           -- l = low, n = nominal, h = high
    daynight,
    source
from read_parquet('{{ var("raw_dir") }}/fires/*/*.parquet')

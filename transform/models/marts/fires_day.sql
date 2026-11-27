-- Crop fires per day in Punjab and Haryana. Only days the satellite data covers
-- appear here, so the latest date shows how fresh the fire data is.
select
    date,
    count(*) as fires,
    count(*) filter (where confidence <> 'l') as fires_confident,
    sum(fire_power_mw) as fire_power_mw
from {{ ref('stg_fires') }}
group by all

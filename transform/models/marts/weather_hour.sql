-- Hourly weather for every city, including the forecast for the next two days.
-- Weather hours fall on :30 India time; `hour` is the air-quality hour they sit
-- in the middle of (e.g. 14:30 belongs to the 14:00-15:00 hour), matching city_hour.
select
    city,
    time_ist,
    cast(time_ist - interval 30 minute as date) as date,
    hour(time_ist - interval 30 minute) as hour,
    * exclude (city, time_ist)
from {{ ref('stg_weather') }}

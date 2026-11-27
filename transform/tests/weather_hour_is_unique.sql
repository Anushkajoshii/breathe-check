select city, time_ist, count(*) as n
from {{ ref('weather_hour') }}
group by all
having n > 1

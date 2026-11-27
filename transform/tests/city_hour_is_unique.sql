select city, time_ist, count(*) as n
from {{ ref('city_hour') }}
group by all
having n > 1

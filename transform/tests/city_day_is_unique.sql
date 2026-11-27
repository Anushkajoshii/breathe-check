-- Each city has at most one row per day
select city, date, count(*) as n
from {{ ref('city_day') }}
group by all
having n > 1

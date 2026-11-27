-- After cleaning, no city average should be impossible
select * from {{ ref('city_day') }}
where pm25 is not null and (pm25 < 1 or pm25 > 999)

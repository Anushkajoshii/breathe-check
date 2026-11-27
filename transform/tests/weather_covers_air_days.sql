-- Every city-day with PM2.5 should have a full day of weather (24 hours)
select city, date, weather_hours from {{ ref('city_day') }}
where pm25 is not null and coalesce(weather_hours, 0) < 24
    -- the first India-time day of the archive starts at 05:30, so it is short
    and date > (select min(cast(time_ist as date)) from {{ ref('stg_weather') }})

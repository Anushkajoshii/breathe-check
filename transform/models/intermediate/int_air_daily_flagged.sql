/*
Daily station readings with a yes/no flag for each way a reading can be wrong.
Nothing is deleted here: the clean tables just leave out flagged rows, and the
quality report counts how many each rule caught.

Rules (numbers are explained in docs/cleaning-rules.md):
  flag_impossible   below 1 or above 999 ug/m3. Monitors top out near 1000,
                    and a whole day under 1 does not happen in Indian cities.
  flag_incomplete   the station reported under two-thirds of the day.
                    India's standard needs 16 of 24 hours for a daily average.
  flag_flat         the value did not move at all over a full day (sd = 0).
                    Real air always moves; this is a stuck sensor.
  flag_repeated     exactly the same daily value three days running.
  flag_city_outlier more than 3 times the median of the city's other
                    stations that day, and at least 100 above it, with at
                    least 3 other stations to compare against.
*/

with base as (
    select
        *,
        pm25 < 1 or pm25 > 999 as flag_impossible,
        coalesce(percent_complete, 0) < 66.7 as flag_incomplete,
        coalesce(pm25_sd, 1) = 0 and coalesce(percent_complete, 0) >= 66.7 as flag_flat,
        pm25 = lag(pm25, 1) over station_days
            and pm25 = lag(pm25, 2) over station_days as flag_repeated_raw
    from {{ ref('stg_air_daily') }}
    window station_days as (partition by location_id order by date)
),

-- The repeat rule should flag all three days of a run, not just the third
repeats as (
    select
        *,
        coalesce(flag_repeated_raw, false)
            or coalesce(lead(flag_repeated_raw, 1) over station_days, false)
            or coalesce(lead(flag_repeated_raw, 2) over station_days, false) as flag_repeated
    from base
    window station_days as (partition by location_id order by date)
),

-- Compare each station with the other usable stations in its city that day
others as (
    select
        a.location_id,
        a.date,
        median(b.pm25) as others_median,
        count(b.pm25) as others_count
    from repeats a
    join repeats b
        on a.city = b.city
        and a.date = b.date
        and a.location_id <> b.location_id
        and not (b.flag_impossible or b.flag_incomplete or b.flag_flat)
    group by all
)

select
    r.city,
    r.location_id,
    r.sensor_id,
    r.date,
    r.pm25,
    r.pm25_sd,
    r.percent_complete,
    r.openaq_flagged,
    o.others_median,
    coalesce(o.others_count, 0) as others_count,
    r.flag_impossible,
    r.flag_incomplete,
    r.flag_flat,
    r.flag_repeated,
    coalesce(
        o.others_count >= 3
        and r.pm25 > 3 * o.others_median
        and r.pm25 - o.others_median > 100,
        false
    ) as flag_city_outlier
from repeats r
left join others o using (location_id, date)

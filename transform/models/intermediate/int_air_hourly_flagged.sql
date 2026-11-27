/*
Hourly station readings with a flag for each problem.

  flag_impossible  below 0 or above 999 ug/m3 (one clean hour can be near 0)
  flag_incomplete  under half of the hour's sub-readings arrived
  flag_stuck       the same value 6 hours in a row
  flag_spike       more than 3 times the median of the 3 hours either side,
                   and at least 150 above it: a jump that comes and goes
                   too fast to be real air
*/

with base as (
    select
        *,
        pm25 < 0 or pm25 > 999 as flag_impossible,
        coalesce(percent_complete, 0) < 50 as flag_incomplete,
        median(pm25) over (
            partition by location_id order by time_ist
            range between interval 3 hour preceding and interval 3 hour following
        ) as nearby_median,
        -- a run of 6 equal values ends at this hour
        count(distinct pm25) over (
            partition by location_id order by time_ist
            range between interval 5 hour preceding and current row
        ) = 1
        and count(*) over (
            partition by location_id order by time_ist
            range between interval 5 hour preceding and current row
        ) = 6 as run_ends_here
    from {{ ref('stg_air_hourly') }}
),

stuck as (
    -- flag every hour in the run, not just the last one
    select
        *,
        bool_or(run_ends_here) over (
            partition by location_id order by time_ist
            range between current row and interval 5 hour following
        ) as flag_stuck
    from base
)

select
    city,
    location_id,
    sensor_id,
    time_ist,
    pm25,
    percent_complete,
    openaq_flagged,
    nearby_median,
    flag_impossible,
    flag_incomplete,
    flag_stuck,
    coalesce(pm25 > 3 * nearby_median and pm25 - nearby_median > 150, false) as flag_spike
from stuck

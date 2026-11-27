-- GRAP is a Delhi-NCR rule; other cities must always show stage 0
select * from {{ ref('city_day') }}
where city_role <> 'grap' and (grap_stage > 0 or original_grap_season)

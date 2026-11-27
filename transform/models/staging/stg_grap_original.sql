select season, cast(start as date) as season_start, cast("end" as date) as season_end
from read_csv('{{ var("reference_dir") }}/grap_original_seasons.csv', header = true)

select year, cast(date as date) as diwali_date
from read_csv('{{ var("reference_dir") }}/diwali.csv', header = true)

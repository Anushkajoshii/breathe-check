select * from read_csv('{{ var("raw_dir") }}/stations.csv', header = true)

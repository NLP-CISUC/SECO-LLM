import polars as pl

df = pl.read_ndjson('results/jokes.jsonl')
sample = df.sample(100, shuffle=True)
sample.write_ndjson('results/evaluation_sample.jsonl')


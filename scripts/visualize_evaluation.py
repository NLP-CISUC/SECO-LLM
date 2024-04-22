from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sn

evaluation_path = Path('results/evaluation/')
evaluation_file = [p for p in evaluation_path.iterdir()][0]

df = pl.read_ndjson(evaluation_file)

insufficient = (df.group_by(pl.col('uuid'))
                  .len()
                  .filter(pl.col('len') < 10)
                  .select(pl.col('uuid'))
                  .to_numpy()
                  .squeeze(1))
df = df.filter(pl.col('uuid').is_in(insufficient).not_())

number_evaluated = (df.group_by([pl.col('uuid'), pl.col('native')])
                      .len()
                      .sort(pl.col('len')))
print(number_evaluated)

agg_df = (df.select(pl.col(['joke_id', 'score']))
            .group_by(pl.col('joke_id'))
            .mean())

print(agg_df.describe())

cmos = agg_df.select('score').mean().item()
cmos_sd = agg_df.select('score').std().item()
print(f'CMOS: {cmos:.4f} +/- {cmos_sd:.4f}')

sn.displot(agg_df.to_pandas(), x='score', kde=True, binrange=(-2, 2))
plt.savefig('results/img/score_hist.pdf')

plt.clf()
sn.boxplot(agg_df.to_pandas(), x='score')
plt.savefig('results/img/score_boxplot.pdf')

from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sn

evaluation_path = Path('results/evaluation/')
evaluation_file = [p for p in evaluation_path.iterdir()][0]
score_df = pl.read_ndjson(evaluation_file)

jokes_path = Path('results/jokes.jsonl')
jokes_df = (pl.read_ndjson(jokes_path)
              .select(pl.col(['id', 'concept', 'part1', 'part2',
                              'relation1', 'relation2', 'joke'])))

seco_path = Path('data/inlg_f1281359_300_man.csv')
seco_df = (pl.read_csv(seco_path)
             .select(pl.col(['_unit_id', 'adivinha']))
             .unique())

insufficient = (score_df.group_by(pl.col('uuid'))
                        .len()
                        .filter(pl.col('len') < 10)
                        .select(pl.col('uuid'))
                        .to_numpy()
                        .squeeze(1))
score_df = score_df.filter(pl.col('uuid').is_in(insufficient).not_())

number_evaluated = (score_df.group_by([pl.col('uuid'), pl.col('native')])
                            .len()
                            .sort(pl.col('len')))
print(number_evaluated)

agg_df = (score_df.select(pl.col(['joke_id', 'score']))
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

(agg_df.join(jokes_df, left_on='joke_id', right_on='id')
       .join(seco_df, left_on='joke_id', right_on='_unit_id')
       .sort(by=pl.col('score'), descending=True)
       .write_ndjson('results/evaluation_scores.jsonl'))

# Generation of Humorous Riddles with Prompt Chaining

This paper focuses on the generaiton of punning riddles with [MariTalk](https://chat.maritaca.ai/) following the rules of [SECO](http://linguamatica.com/index.php/linguamatica/article/view/268). We then provide a comparison between the two systems and show that they do not differ significantly in terms of funniness.

## Install

To install the project, you can use `pipenv`.

```bash
pipenv install
```

Or by using `pip`.

```bash
pip install -r requirements.txt
```

## Run

The entire project is in the `SECO-LLM/scripts` folder. The scripts are as follows:

- `generate_llm.py`: Provides the humor generation prompt chaining, by using MariTalk with an active API key stored in `.env`.
- `sample_evaluation.py`: Random sampling of 100 jokes for evaluation.
- `evaluation_interface.py`: CMOS evaluation interface created with [Gradio](https://www.gradio.app/).
- `visualize_evaluation.py`: Compute metrics and images for analysing the evaluation results.
- `stat_test.R`: Do statistical significance testing.

## Results

All results can be found in the `SECO-LLM/results` folder. The folder is organized as follows:

- `evaluation/evaluation_2024_04_16_15_55_49.jsonl`: Contains all evaluation results. Each evaluator has a single `uuid` and evaluates joke pairs with unique `joke_id`. The `score` sign is already corrected (negative values always represent a preference for SECO).
- `img/`: Images created for the paper.
- `jokes.jsonl`: All results from the LLM.Contains the input concept, its sub-words, relations used, all prompts and responses, and the final LLM joke in column `joke`.
- `evaluation_sample.jsonl`: Sample of 100 jokes used for evaluation.
- `evaluation_scores.jsonl`: Evaluation result. Contains the LLM joke in column `joke`, and SECO's original riddle in `adivinha`. The final `score` already aggregates all evaluators' opinions.
- `stat_test.txt`: Significance testing results.

## How to cite

```bibtex
To be determined
```

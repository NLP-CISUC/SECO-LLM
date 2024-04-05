import os
import re
from time import sleep
from typing import Tuple

import dotenv
import polars as pl
from maritalk import MariTalk
from maritalk.resources.api import MaritalkHTTPError

dotenv.load_dotenv()
split_lexicon = pl.read_csv('../../Resources/Lexica/SECO/aglut_lexico_v2.txt',
                            separator='\t')
llm = MariTalk(key=os.environ['MARITALK_API_KEY'],
               model='sabia-2-small')


def run_llm(messages):
    answer = None
    while answer is None:
        try:
            answer = llm.generate(messages, temperature=0.2)['answer']
        except MaritalkHTTPError as error:
            print('Waiting server...')
            sleep(15)
    return answer


def get_concept_parts(row: Tuple):
    part1, part2 = list(), list()
    _, _, _, _, _, type_, concept = row
    if type_ in ['sem-compounds', 'compounds']:
        part1, part2 = re.split(r'[ -]', concept)
        part1, part2 = [part1], [part2]
    else:
        parts = (split_lexicon.filter(pl.col('#Termo') == concept)
                 .select(pl.col(['P1', 'P2']))
                 .to_numpy().T)
        part1, part2 = parts
    return part1, part2


RELATION_NAMES = {'antonimo': 'antônimos',
                  'ANTONIMO_ADJ_DE': 'antônimos',
                  'HIPERONIMO_DE': 'hipônimos',
                  'SINONIMO_ADJ_DE': 'sinônimos',
                  'LOCAL_ORIGEM_DE': 'locais',
                  'DIZ_SE_SOBRE': 'assuntos',
                  'MEMBRO_DE': 'grupos',
                  'FINALIDADE_DE': 'propósitos',
                  'PARTE_DE_ALGO_COM_PROPRIEDADE': 'elementos constituintes',
                  'PARTE_DE': 'elementos constituintes',
                  'FAZ_SE_COM': 'meios de execução',
                  'ACCAO_QUE_CAUSA': 'efeitos'}
CONCEPT_REGEX = (r'(?:Qual é o contrário de|O que significa' +
                 r'|Que resulta do cruzamento entre.*\?) ([^.?]*)(?:\?|\.)')

seco_results = pl.read_csv('../../Literature_methods/Humor_Hugo/Humor/' +
                           'resultados_crowflower/inlg_f1281359_300_man.csv')
seco_results = seco_results.filter(pl.col('origem')
                                     .is_in(['antonimos-1', 'amalg'])
                                     .not_())

seco_scores = (seco_results.select(pl.col(['_unit_id', 'potencial_humorstico']))
                           .group_by('_unit_id').median()
                           .join(seco_results.select(pl.col(['_unit_id',
                                                             'adivinha',
                                                             'relacao_1',
                                                             'relacao_2',
                                                             'origem'])),
                                 on='_unit_id', how='inner')
                           .unique()
                           .with_columns(pl.col('adivinha')
                                           .str.extract(CONCEPT_REGEX)
                                           .alias('conceito')))

seco_scores[['p1', 'p2']] = seco_scores.map_rows(get_concept_parts)

# Prompt templates
system_prompt = ('Você é um assistente com um grande senso de humor ' +
                 'que adora criar trocadilhos e jogos de palavras ' +
                 'engraçados. Você vai ajudar o usuário a seguir um ' +
                 'raciocínio passo-a-passo para gerar um trocadilho, ' +
                 'jogos de palavras, ou piadas relacionados àquele tópico. ' +
                 'A piada deve ser original, criativa e fazer o leitor rir.')
step1_template = ('Observe essa palavra: {concept}. Ela pode ser dividida ' +
                  'em duas partes: {part1}; e {part2}. ' +
                  'Quais são os {relation1} de {part1} ' +
                  'e os {relation2} de {part2}?')
step2_template = ('Crie uma lista de piadas em forma de pergunta e resposta ' +
                  'que combinem {concept} com os {relation1} de {part1} ' +
                  'e os {relation2} de {part2}. A piada deve seguir' +
                  ', em linhas gerais, o seguinte modelo: "{template}".')
step3_template = ('Dessa lista de piadas, escolha somente uma que seja ' +
                  'a mais engraçada e que faça o maior número de pessoas ' +
                  'rir. Apresente o texto da piada incluindo a pergunta ' +
                  'do modelo, sem mais informações.')


results = {'concept': list(), 'part1': list(), 'part2': list(),
           'relation1': list(), 'relation2': list(),
           'prompt1': list(), 'relationed_words': list(),
           'prompt2': list(), 'candidates': list(),
           'prompt3': list(), 'joke': list()}
for row in seco_scores.iter_rows():
    if row[2].startswith('Qual é o contrário'):
        joke_template = f'Qual é o contrário de {row[6]}? X'
    elif row[2].startswith('O que significa'):
        joke_template = f'O que significa {row[6]}? X'
    else:
        joke_template = f'Que resulta do cruzamento entre X e Y ? {row[6]}'

    prompt1 = step1_template.format(concept=row[6],
                                    part1=', '.join(row[7]),
                                    part2=', '.join(row[8]),
                                    relation1=RELATION_NAMES[row[3]],
                                    relation2=RELATION_NAMES[row[4]])
    prompt2 = step2_template.format(relation1=RELATION_NAMES[row[3]],
                                    part1=', '.join(row[7]),
                                    relation2=RELATION_NAMES[row[4]],
                                    part2=', '.join(row[8]),
                                    concept=row[6],
                                    template=joke_template)
    prompt3 = step3_template

    # Get relations
    messages = [{'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt1}]
    relations_answer = run_llm(messages)
    messages.append({'role': 'assistant', 'content': relations_answer})

    # Generate joke candidates
    messages.append({'role': 'user', 'content': prompt2})
    candidates_answer = run_llm(messages)
    messages.append({'role': 'assistant', 'content': candidates_answer})

    # Select best joke
    messages.append({'role': 'user', 'content': step3_template})
    final_answer = run_llm(messages)

    results['concept'].append(row[6])
    results['part1'].append(', '.join(row[7]))
    results['part2'].append(', '.join(row[8]))
    results['relation1'].append(row[3])
    results['relation2'].append(row[4])
    results['prompt1'].append(prompt1)
    results['relationed_words'].append(relations_answer)
    results['prompt2'].append(prompt2)
    results['candidates'].append(candidates_answer)
    results['prompt3'].append(prompt3)
    results['joke'].append(final_answer)

results_df = pl.DataFrame(results)
results_df.write_ndjson('results/jokes.jsonl')

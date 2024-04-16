import json
import random
import uuid
from datetime import datetime

import gradio as gr
import polars as pl

jokes_df = pl.read_ndjson('results/evaluation_sample.jsonl')
seco_df = pl.read_csv('data/inlg_f1281359_300_man.csv')
seco_df = seco_df.select(pl.col(['_unit_id', 'adivinha'])).unique()
df = jokes_df.join(seco_df, left_on='id', right_on='_unit_id')


def get_timestamp(): return datetime.now().strftime('%Y_%m_%d_%H_%M_%S')


filename = f'results/evaluation/evaluation_{get_timestamp()}.jsonl'


def sample_random(state): 
    iteration = state['iteration']
    row = df.row(iteration % len(df), named=True)
    state['joke_id'] = row['id']
    state['seco_left'] = True if random.randint(0, 1) == 1 else False

    Left = row['adivinha'] if state['seco_left'] else row['joke']
    Right = row['joke'] if state['seco_left'] else row['adivinha']
    state['iteration'] += 1
    return (Left, Right, gr.update(visible=True), gr.update(interactive=False),
            gr.update(interactive=False), state)


def vote(score, state_vars, left_text, right_text, native):
    result = {'timestamp': get_timestamp(),
              'uuid': state_vars['uid'],
              'joke_id': state_vars['joke_id'],
              'seco_left': state_vars['seco_left'],
              'score': score if state_vars['seco_left'] else -score,
              'native': native}
    if not left_text or not right_text: return (None, None)
    with open(filename, 'a+', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False))
        f.write('\n')
    left, right, _, _, _, state_vars = sample_random(state_vars)
    interactive = False if state_vars['iteration'] == len(df) else True
    return (left, right, 0, gr.update(value=state_vars['iteration']),
            state_vars, gr.update(interactive=interactive))


def init_state():
    return {'joke_id': 0, 'iteration': 0, 'seco_left': False,
            'uid': str(uuid.uuid4())}


with gr.Blocks() as demo:
    state_vars = gr.State(init_state)

    gr.Markdown('# Geração Automática de Humor\n\n'
                'Esse estudo objetiva avaliar as preferências de utilizadores humanos '
                'relativamente a dois sistemas automáticos de geração de adivinhas.\n\n'
                'Serão apresentadas duas adivinhas, **Direita** e **Esquerda**, '
                'você deverá comparar os textos entre si e indicar em uma escala '
                'qual adivinha é melhor. A pontuação deve refletir o quão boa é a '
                'piada (não foque em avaliar se o texto está gramaticalmente correto).\n\n' 'Quando submeter o voto, um novo par será apresentado para avaliação.\n\n'
                '**Por favor, indique se você é um falante nativo de português clicando '
                'na caixa de seleção.**\n\n'
                'Quando estiver pronto para começar a avaliação, clique no botão '
                '**Iniciar** abaixo.')
    native = gr.Checkbox(label='Eu sou um falante nativo de português.')
    start_btn = gr.Button(value='Iniciar')

    with gr.Column(visible=False) as col1:
        gr.Markdown('## Avaliação')

        gr.HTML(
            '''
        <div style="display: flex; justify-content: center; margin-top: 20px;align-items: center;">
            <ul style="list-style: none;">
                <li style="display: inline-block; margin-right:35px;">-2 - Esquerda é melhor</li> <li style="display: inline-block; margin-right:35px;">-1 - Esquerda é levemente melhor</li>
                <li style="display: inline-block; margin-right:35px;">0 - Ambas são iguais</li>
                <li style="display: inline-block; margin-right:35px;">1 - Direita é levemente melhor</li>
                <li style="display: inline-block; margin-right:35px;">2 - Direita é melhor</li>
            </ul>
        </div>
        ''')
        
        progress = gr.Slider(0, len(df), label='Progresso', interactive=False,
                             container=False)

        gr.HTML(
            '''
        <div style="display: flex; justify-content: center;margin-top: 20px;align-items: center;">
            <div style="text-align: left;font-size: medium;">Esquerda é melhor</div>
                <svg fill="#ffffff" height="5vh" width="200px" version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 512.04 512.04" xml:space="preserve" stroke="#ffffff">
                    <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
                    <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
                    <g id="SVGRepo_iconCarrier"> <g> <g>
                        <path d="M508.933,248.353L402.267,141.687c-4.267-4.053-10.987-3.947-15.04,0.213c-3.947,4.16-3.947,10.667,0,14.827 l88.427,88.427H36.4l88.427-88.427c4.053-4.267,3.947-10.987-0.213-15.04c-4.16-3.947-10.667-3.947-14.827,0L3.12,248.353 c-4.16,4.16-4.16,10.88,0,15.04L109.787,370.06c4.267,4.053,10.987,3.947,15.04-0.213c3.947-4.16,3.947-10.667,0-14.827 L36.4,266.593h439.147L387.12,355.02c-4.267,4.053-4.373,10.88-0.213,15.04c4.053,4.267,10.88,4.373,15.04,0.213 c0.107-0.107,0.213-0.213,0.213-0.213l106.667-106.667C513.093,259.34,513.093,252.513,508.933,248.353z"></path>
                    </g> </g> </g>
                </svg>
            <div style="text-align: right;font-size: medium;">Direita é melhor</div>
        </div>''')

        with gr.Row():
            left_text = gr.Textbox(label='Esquerda', interactive=False)
            score = gr.Slider(minimum=-2, maximum=2, step=1,
                              value=0, info='Avaliação')
            right_text = gr.Textbox(label='Direita', interactive=False)
        vote_btn = gr.Button(value='Submeter voto')

    start_btn.click(
        fn=sample_random,
        inputs=[state_vars],
        outputs=[left_text, right_text, col1, start_btn, native, state_vars]
    )

    vote_btn.click(
        fn=vote,
        inputs=[score, state_vars, left_text, right_text, native],
        outputs=[left_text, right_text, score, progress, state_vars, vote_btn]
    )


demo.launch(server_name='nlp.dei.uc.pt', server_port=8080)

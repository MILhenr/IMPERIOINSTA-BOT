import os
import shutil
import subprocess
import atexit
import numpy as np
from moviepy.editor import (
    VideoFileClip, CompositeVideoClip, AudioClip, ColorClip, ImageClip
)
import random

# Impede o Mac de hibernar durante o processamento
caffeinate_process = subprocess.Popen(['caffeinate'])
atexit.register(caffeinate_process.terminate)

downloads_folder = os.path.expanduser('~/Downloads')
destino_pasta = os.path.expanduser('~/Desktop/ModoGoleiro')
os.makedirs(destino_pasta, exist_ok=True)

# 🔁 Move e renomeia vídeos com nome aleatório de M1 a M40
arquivos = sorted(
    [f for f in os.listdir(downloads_folder) if f.lower().endswith(('.mp4', '.mov'))],
    key=lambda f: os.path.getmtime(os.path.join(downloads_folder, f))
)

for arquivo in arquivos:
    origem = os.path.join(downloads_folder, arquivo)

    numeros_usados = []
    for f in os.listdir(destino_pasta):
        if f.startswith('G') and f[1:-4].isdigit():
            numeros_usados.append(int(f[1:-4]))

    disponiveis = list(set(range(1, 41)) - set(numeros_usados))

    if not disponiveis:
        print('Todos os nomes de G1 a G50 estão ocupados!')
        exit()

    numero_sorteado = random.choice(disponiveis)
    novo_nome = f'MG{numero_sorteado}{os.path.splitext(arquivo)[1]}'

    destino = os.path.join(destino_pasta, novo_nome)
    shutil.move(origem, destino)
    print(f'🎥 {arquivo} movido e renomeado para {novo_nome}')

# 🎬 Edição dos vídeos movidos
pasta = destino_pasta
pasta_saida = os.path.join(pasta, 'GoleiroEditado')
os.makedirs(pasta_saida, exist_ok=True)

fundos = [
    os.path.join(pasta, 'EXEMPLOG1.MOV'),
    os.path.join(pasta, 'EXEMPLOG2.MOV'),
    os.path.join(pasta, 'EXEMPLOG3.MOV')
]

# Funções auxiliares
def gerar_nome_unico(base_nome, extensao, pasta_destino):
    contador = 0
    novo_nome = f'{base_nome}.{extensao}'
    while os.path.exists(os.path.join(pasta_destino, novo_nome)):
        contador += 1
        novo_nome = f'{base_nome}_{contador}.{extensao}'
    return novo_nome

def gerar_ding_audio(duration=0.3, freq=440, fps=44100):
    def make_sound(t):
        wave = 0.1 * np.sin(2 * np.pi * freq * t) * np.exp(-15 * t)
        return wave if isinstance(t, np.ndarray) else float(wave)
    return AudioClip(make_sound, duration=duration, fps=fps)

def combinar_audios(audio1, audio2, duracao):
    fps = audio1.fps
    def make_frame(t):
        t = np.array([t]) if isinstance(t, (float, int)) else t
        frame1 = audio1.get_frame(t)
        frame2 = audio2.get_frame(t)

        frame1 = frame1.reshape(-1, 1) if frame1.ndim == 1 else frame1
        frame2 = frame2.reshape(-1, 1) if frame2.ndim == 1 else frame2

        min_len = min(frame1.shape[0], frame2.shape[0])
        frame1 = frame1[:min_len]
        frame2 = frame2[:min_len]

        mixed = np.clip(frame1 + frame2, -1, 1)
        return mixed.squeeze()
    return AudioClip(make_frame, duration=duracao, fps=fps)

videos_mf = sorted([
    f for f in os.listdir(pasta)
    if f.startswith('MG') and f.lower().endswith(('.mp4', '.mov'))
])

for video_nome in videos_mf:
    caminho_video = os.path.join(pasta, video_nome)
    print(f'🔧 Editando {video_nome}...')

    # 🔁 Escolher fundo ALEATÓRIO para cada vídeo
    fundo_path = random.choice(fundos)
    fundo = VideoFileClip(fundo_path).without_audio()
 

    # Ajustes com base no fundo escolhido
    if 'EXEMPLOG1' in fundo_path:
        altura_resize = fundo.h * 0.6
        posicao_y = 1300
    elif 'EXEMPLOG2' in fundo_path:
        altura_resize = fundo.h * 0.57
        posicao_y = 1230
    elif 'EXEMPLOG3' in fundo_path:
        altura_resize = fundo.h * 0.57
        posicao_y = 1330
    else:
        altura_resize = fundo.h * 0.45
        posicao_y = 1250

    video = VideoFileClip(caminho_video)
    lado_quadrado = min(video.w, video.h)
    video_quadrado = video.crop(
        x_center=video.w / 2,
        y_center=video.h / 2,
        width=lado_quadrado,
        height=lado_quadrado
    )

    video_redimensionado = video_quadrado.resize(height=altura_resize)
    video_redimensionado = video_redimensionado.set_position(('center', posicao_y))

    camada_transparente = ColorClip(size=video_redimensionado.size, color=(0, 0, 0), duration=video.duration)
    camada_transparente = camada_transparente.set_opacity(0.02).set_position(('center', 1140))

    # ✅ Tratamento para vídeos sem áudio
    if video.audio is not None:
        audio_original = video.audio.set_duration(video.duration)
    else:
        audio_original = AudioClip(lambda t: 0, duration=video.duration, fps=44100)

    ding_audio = gerar_ding_audio(duration=0.3).set_start(1.5)

    duracao_final = min(fundo.duration, video.duration)
    audio_final = combinar_audios(audio_original, ding_audio, duracao_final)

    elementos = [fundo, video_redimensionado, camada_transparente]

    video_final = CompositeVideoClip(elementos).subclip(0, duracao_final).set_audio(audio_final)

    base_nome = 'E' + os.path.splitext(video_nome)[0] + '_editado'
    nome_editado_final = gerar_nome_unico(base_nome, 'mp4', pasta_saida)
    caminho_salvar = os.path.join(pasta_saida, nome_editado_final)

    video_final.write_videofile(
        caminho_salvar,
        codec='libx264',
        threads=4,
        audio_codec='aac',
        preset='ultrafast',
        fps=29.9,
        bitrate=None,
        ffmpeg_params=['-crf', '18']
    )

    video.close()
    video_final.close()
    fundo.close()
    os.remove(caminho_video)
    print(f'✅ {video_nome} editado e deletado com sucesso.')

print('🎉 Todos os vídeos foram editados e salvos na pasta ModoGoleiro!')
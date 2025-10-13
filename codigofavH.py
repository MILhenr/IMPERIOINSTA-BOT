import os
import shutil
import subprocess
import atexit
import numpy as np
from moviepy.editor import (
    VideoFileClip, CompositeVideoClip, AudioClip, ColorClip, ImageClip
)
import random

# Evita suspensão do Mac
caffeinate_process = subprocess.Popen(['caffeinate'])
atexit.register(caffeinate_process.terminate)

downloads_folder = os.path.expanduser('~/Downloads')
destino_pasta = os.path.expanduser('~/Desktop/FavelaHoje')
os.makedirs(destino_pasta, exist_ok=True)

# Move todos os vídeos da pasta Downloads
videos_novos = [
    f for f in os.listdir(downloads_folder)
    if f.lower().endswith(('.mp4', '.mov'))
]

numeros_usados = [
    int(f[1:-4]) for f in os.listdir(destino_pasta)
    if f.startswith('FH') and f[1:-4].isdigit()
]

indice = 1
for video in sorted(videos_novos):
    while indice in numeros_usados:
        indice += 1
    novo_nome = f'FH{indice}{os.path.splitext(video)[1]}'
    origem = os.path.join(downloads_folder, video)
    destino = os.path.join(destino_pasta, novo_nome)
    shutil.move(origem, destino)
    print(f'Vídeo {video} movido como {novo_nome}')
    indice += 1

# Pastas e caminhos
pasta_saida = os.path.join(destino_pasta, 'FavelaHoje')
os.makedirs(pasta_saida, exist_ok=True)

fundos = [
    os.path.join(destino_pasta, 'fundoFH1.MOV'),
    os.path.join(destino_pasta, 'fundoFH2.MOV'),
]

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
        f1, f2 = audio1.get_frame(t), audio2.get_frame(t)
        f1 = f1.reshape(-1, 1) if f1.ndim == 1 else f1
        f2 = f2.reshape(-1, 1) if f2.ndim == 1 else f2
        mixed = np.clip(f1 + f2, -1, 1)
        return mixed.squeeze()
    return AudioClip(make_frame, duration=duracao, fps=fps)

# Processa vídeos
videos_para_editar = sorted([
    f for f in os.listdir(destino_pasta)
    if f.startswith('FH') and f.lower().endswith(('.mp4', '.mov'))
])

for video_nome in videos_para_editar:
    caminho_video = os.path.join(destino_pasta, video_nome)
    print(f'Editando {video_nome}...')

    # Escolhe fundo aleatório
    fundo_path = random.choice(fundos)
    fundo = VideoFileClip(fundo_path).without_audio()

    # Ajusta posição/redimensionamento
    if 'fundoFH1' in fundo_path:
        altura_resize = fundo.h * 0.56
        posicao_y = 1300
    elif 'fundoFH2' in fundo_path:
        altura_resize = fundo.h * 0.56
        posicao_y = 1350
    else:
        altura_resize = fundo.h * 0.45
        posicao_y = 1220

    duracao_final = None

    video = VideoFileClip(caminho_video)
    lado_quadrado = min(video.w, video.h)
    video_crop = video.crop(
        x_center=video.w / 2,
        y_center=video.h / 2,
        width=lado_quadrado,
        height=lado_quadrado
    )
    video_editado = video_crop.resize(height=altura_resize)
    video_editado = video_editado.set_position(("center", posicao_y))

    camada_transparente = ColorClip(
        size=video_editado.size,
        color=(0, 0, 0),
        duration=video.duration
    ).set_opacity(0.02).set_position(('center', 1140))

    audio_original = video.audio.set_duration(video.duration)
    ding_audio = gerar_ding_audio(duration=0.3).set_start(1.5)

    duracao_final = min(fundo.duration, video.duration)
    audio_final = combinar_audios(audio_original, ding_audio, duracao_final)

    elementos = [fundo, video_editado, camada_transparente]

    video_final = CompositeVideoClip(elementos).subclip(0, duracao_final)
    video_final = video_final.set_audio(audio_final)

    nome_final = gerar_nome_unico(f'E{os.path.splitext(video_nome)[0]}_editado', 'mp4', pasta_saida)
    caminho_final = os.path.join(pasta_saida, nome_final)

    video_final.write_videofile(
        caminho_final,
        codec='libx264',
        threads=4,
        audio_codec='aac',
        preset='ultrafast',
        fps=29.9,
        ffmpeg_params=['-crf', '18']
    )

    video.close()
    video_final.close()
    fundo.close()
    os.remove(caminho_video)
    print(f'{video_nome} editado e removido.')

print("✅ Todos os vídeos foram processados!")
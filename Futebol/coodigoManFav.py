import os
import shutil
import subprocess
import atexit
import numpy as np
from moviepy.editor import (
    VideoFileClip, CompositeVideoClip, AudioClip, ColorClip
)
import random
from multiprocessing import Pool, cpu_count

# 🔒 Impede o Mac de dormir
caffeinate_process = subprocess.Popen(['caffeinate'])
atexit.register(caffeinate_process.terminate)

downloads_folder = os.path.expanduser('~/Downloads')
destino_pasta = os.path.expanduser('~/Desktop/manuFAVELA')
os.makedirs(destino_pasta, exist_ok=True)

# 🔁 Move e renomeia vídeos
arquivos = sorted(
    [f for f in os.listdir(downloads_folder) if f.lower().endswith(('.mp4', '.mov'))],
    key=lambda f: os.path.getmtime(os.path.join(downloads_folder, f))
)

for arquivo in arquivos:
    origem = os.path.join(downloads_folder, arquivo)

    numeros_usados = []
    for f in os.listdir(destino_pasta):
        if f.startswith('MANUFAV') and f[2:-4].isdigit():
            numeros_usados.append(int(f[2:-4]))

    disponiveis = list(set(range(1, 41)) - set(numeros_usados))

    if not disponiveis:
        print('Todos os nomes de MANUFAV1 a MANUFAV40 estão ocupados!')
        exit()

    numero_sorteado = random.choice(disponiveis)
    novo_nome = f'MANUFAV{numero_sorteado}{os.path.splitext(arquivo)[1]}'

    destino = os.path.join(destino_pasta, novo_nome)
    shutil.move(origem, destino)
    print(f'🎥 {arquivo} movido e renomeado para {novo_nome}')

# 🎬 Edição
pasta = destino_pasta
pasta_saida = os.path.join(pasta, 'ManuFavelaEditado')
os.makedirs(pasta_saida, exist_ok=True)

fundos = [
    os.path.join(pasta, 'fundoMFavela.MOV')
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
        frame1 = audio1.get_frame(t)
        frame2 = audio2.get_frame(t)

        frame1 = frame1.reshape(-1, 1) if frame1.ndim == 1 else frame1
        frame2 = frame2.reshape(-1, 1) if frame2.ndim == 1 else frame2

        min_len = min(frame1.shape[0], frame2.shape[0])
        mixed = np.clip(frame1[:min_len] + frame2[:min_len], -1, 1)
        return mixed.squeeze()
    return AudioClip(make_frame, duration=duracao, fps=fps)

def limpar_digital_moviepy(caminho_input, caminho_output):
    cmd = [
        'ffmpeg', '-y', '-i', caminho_input,
        '-c', 'copy',
        '-movflags', '+faststart',
        '-metadata', 'encoder=Lavf59.27.100',
        '-metadata', 'com.apple.quicktime.make=Apple',
        '-metadata', 'com.apple.quicktime.model=iPhone 14',
        caminho_output
    ]
    subprocess.run(cmd)

videos_mf = sorted([
    f for f in os.listdir(pasta)
    if f.startswith('MANUFAV') and f.lower().endswith(('.mp4', '.mov'))
])

for video_nome in videos_mf:
    caminho_video = os.path.join(pasta, video_nome)
    print(f'🔧 Editando {video_nome}...')

    fundo_path = random.choice(fundos)
    if not os.path.exists(fundo_path):
        print(f'⚠️ Fundo não encontrado: {fundo_path}. Pulando vídeo.')
        continue
    fundo = VideoFileClip(fundo_path).without_audio()

    if 'fundoMFavela' in fundo_path:
        altura_resize = fundo.h * 0.6
        posicao_y = 1350
    else:
        altura_resize = fundo.h * 0.45
        posicao_y = 1220

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

    audio_original = video.audio.set_duration(video.duration) if video.audio else AudioClip(lambda t: 0, duration=video.duration, fps=44100)
    ding_audio = gerar_ding_audio(duration=0.3).set_start(1.5)

    duracao_final = min(fundo.duration, video.duration)
    audio_final = combinar_audios(audio_original, ding_audio, duracao_final)

    elementos = [fundo, video_redimensionado, camada_transparente]

    video_final = CompositeVideoClip(elementos).subclip(0, duracao_final).set_audio(audio_final)

    base_nome = 'B' + os.path.splitext(video_nome)[0] + '_editado'
    nome_editado_final = gerar_nome_unico(base_nome, 'mp4', pasta_saida)
    caminho_salvar = os.path.join(pasta_saida, nome_editado_final)

    try:
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
        video_final.close()
        video.close()
        fundo.close()

        # 🔒 Limpeza para tirar rastro do MoviePy
        caminho_limpo = caminho_salvar.replace('_editado.mp4', '_pronto.mp4')
        limpar_digital_moviepy(caminho_salvar, caminho_limpo)
        os.remove(caminho_salvar)

        print(f'✅ {video_nome} editado e salvo como {os.path.basename(caminho_limpo)}')
        os.remove(caminho_video)
    except Exception as e:
        print(f'❌ Erro ao salvar {video_nome}: {e}')

print('🎉 Todos os vídeos foram processados!')
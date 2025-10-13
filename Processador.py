import os
import shutil
import subprocess
import random
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeAudioClip,
    ColorClip, CompositeVideoClip, vfx
)
import numpy as np

# CAMINHOS AJUSTE AQUI
PASTA_BRUTOS = "/Users/HenryMoney/Downloads"
PASTA_WORK = "/Users/HenryMoney/Desktop/FAVELA/Processados"
DING_AUDIO = "/Users/HenryMoney/Desktop/FAVELA/ding.mp3"  # coloque um ding aqui

# MAPEAMENTO DE NOMES PARA SCRIPTS
MAPEAMENTO = {
    "fh": "Favelahoje.py",
}

print("🚀 SCRIPT INICIADO")

# VERIFICA SE A PASTA DE ENTRADA EXISTE
if not os.path.exists(PASTA_BRUTOS):
    print(f"❌ A pasta de vídeos brutos não existe: {PASTA_BRUTOS}")
    exit(1)

# CRIA A PASTA DE SAÍDA SE NÃO EXISTIR
os.makedirs(PASTA_WORK, exist_ok=True)

print(f"📂 Lendo vídeos de: {PASTA_BRUTOS}")

# VÍDEOS .MP4 E .MOV
videos = [f for f in os.listdir(PASTA_BRUTOS) if f.lower().endswith((".mp4", ".mov"))]

if not videos:
    print("⚠️ Nenhum vídeo .mp4 ou .mov encontrado na pasta.")
    exit(0)

# LOOP DOS VÍDEOS
for video_original in videos:
    caminho_original = os.path.join(PASTA_BRUTOS, video_original)
    nome_base, extensao = os.path.splitext(video_original)

    for sufixo, script in MAPEAMENTO.items():
        nome_novo = f"{nome_base}_{sufixo}{extensao}"
        caminho_novo = os.path.join(PASTA_WORK, nome_novo)

        print(f"\n📄 Copiando: {video_original} → {nome_novo}")
        shutil.copy2(caminho_original, caminho_novo)

        # --- PROCESSAR AUDIO + OVERLAY TRANSPARENTE + ALTERAÇÕES ---
        try:
            print("🎵 Alterando áudio + aplicando múltiplas camadas de proteção...")

            video = VideoFileClip(caminho_novo)

            # 🔊 Áudio original
            audio_original = video.audio

            # 🎵 Ding no início + leve alteração no pitch
            if os.path.exists(DING_AUDIO):
                ding = AudioFileClip(DING_AUDIO).volumex(0.6).set_start(0)
                audio_final = CompositeAudioClip([audio_original.volumex(1.01), ding])
            else:
                audio_final = audio_original.volumex(1.02)

            # Pequeno shift de áudio (100ms atraso)
            audio_final = audio_final.set_start(0.1)

            video = video.set_audio(audio_final)

            # 🎬 Leve modificação de velocidade
            fator = random.choice([0.999, 1.001])  # quase imperceptível
            video = video.fx(vfx.speedx, factor=fator)

            # 🎨 Overlay transparente variável
            cor = random.choice([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
            overlay = ColorClip(size=video.size, color=cor, duration=video.duration)
            overlay = overlay.set_opacity(0.015)

            # Marca d'água invisível dinâmica (aparece rápido em alguns frames)
            marca = ColorClip(size=(50, 50), color=(5, 5, 5), duration=0.2).set_opacity(0.02)
            marca = marca.set_position(("right", "bottom")).set_start(3)
            overlays = [overlay, marca]

            # Combinar tudo
            video_com_overlay = CompositeVideoClip([video] + overlays)

            # Salvar com qualidade quase lossless
            caminho_modificado = caminho_novo.replace(extensao, "_final.mp4")
            video_com_overlay.write_videofile(
                caminho_modificado,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",
                ffmpeg_params=["-crf", "18"],
                threads=4
            )

            os.remove(caminho_novo)
            os.rename(caminho_modificado, caminho_novo)

            print("✅ Alterações seguras aplicadas.")
        except Exception as e:
            print(f"❌ Erro ao modificar áudio/vídeo: {e}")

        # --- RODAR SCRIPT ESPECÍFICO ---
        caminho_script = os.path.join("/Users/HenryMoney/Desktop/FAVELA", script)
        print(f"🔧 Executando: {script} com {nome_novo}")
        subprocess.run(["python", caminho_script, caminho_novo])

    # Depois que rodou todos os scripts, apaga o original da pasta Downloads
    try:
        os.remove(caminho_original)
        print(f"🗑️ Vídeo original {video_original} apagado da pasta Downloads.")
    except Exception as e:
        print(f"❌ Erro ao apagar {video_original}: {e}")

print("\n✅ TODOS OS VÍDEOS PROCESSADOS COM SUCESSO.")
import cv2
import numpy as np
import os
import imageio_ffmpeg
import subprocess
from pydub.generators import Sine
from pydub import AudioSegment


def gerar_ding_audio(output_path="ding.wav", duration=0.3, freq=440):
    """Gera um som 'ding' e salva como WAV."""
    ding = Sine(freq).to_audio_segment(duration=duration * 1000).apply_gain(-12)
    ding.export(output_path, format="wav")
    return output_path


def combinar_audios(audio_path1, audio_path2, output_path="audio_final.wav"):
    """Combina dois áudios (original + ding)."""
    audio1 = AudioSegment.from_file(audio_path1)
    audio2 = AudioSegment.from_file(audio_path2)
    audio2 = audio2.overlay(audio1)
    audio2.export(output_path, format="wav")
    return output_path


def processar_video(input_path, output_path):
    fundo_path = os.path.expanduser("~/Desktop/InstaManual/EXEMPLOM4.MOV")
    temp_sem_audio = "temp_sem_audio.mp4"
    temp_audio_original = "temp_audio_original.wav"
    temp_ding = gerar_ding_audio()
    temp_audio_final = "temp_audio_final.wav"

    # Extrair áudio original do vídeo
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-vn", "-acodec", "pcm_s16le", temp_audio_original],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Combinar áudios
    combinar_audios(temp_audio_original, temp_ding, temp_audio_final)

    # Abrir fundo e vídeo principal
    cap_fundo = cv2.VideoCapture(fundo_path)
    cap_video = cv2.VideoCapture(input_path)

    fps = int(cap_video.get(cv2.CAP_PROP_FPS))
    fundo_width = int(cap_fundo.get(cv2.CAP_PROP_FRAME_WIDTH))
    fundo_height = int(cap_fundo.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Criar escritor
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_sem_audio, fourcc, fps, (fundo_width, fundo_height))

    altura_resize = int(fundo_height * 0.45)
    posicao_y = 1220

    while True:
        ret_f, frame_fundo = cap_fundo.read()
        ret_v, frame_video = cap_video.read()

        if not ret_f or not ret_v:
            break

        # Crop quadrado do vídeo original
        h, w, _ = frame_video.shape
        lado = min(w, h)
        x0 = (w - lado) // 2
        y0 = (h - lado) // 2
        frame_video = frame_video[y0:y0 + lado, x0:x0 + lado]

        # Redimensionar o vídeo recortado
        frame_video = cv2.resize(frame_video, (altura_resize, altura_resize))

        # Inserir no fundo
        x = (fundo_width - altura_resize) // 2
        y = min(posicao_y, fundo_height - altura_resize)
        frame_fundo[y:y + altura_resize, x:x + altura_resize] = frame_video

        # Camada transparente
        overlay = frame_fundo.copy()
        cv2.rectangle(overlay, (x, y), (x + altura_resize, y + altura_resize), (0, 0, 0), -1)
        frame_final = cv2.addWeighted(overlay, 0.02, frame_fundo, 0.98, 0)

        out.write(frame_final)

    cap_fundo.release()
    cap_video.release()
    out.release()

    # Combinar o vídeo final com o áudio final
    subprocess.run([
        "ffmpeg", "-y", "-i", temp_sem_audio, "-i", temp_audio_final,
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-shortest", output_path
    ])

    # Limpeza
    for f in [temp_sem_audio, temp_audio_original, temp_ding, temp_audio_final]:
        if os.path.exists(f):
            os.remove(f)

    print(f"✅ Vídeo processado salvo em: {output_path}")
import os
import numpy as np
from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioClip, ColorClip

def gerar_ding_audio(duration=0.3, freq=440, fps=44100):
    def make_sound(t):
        wave = 0.1 * np.sin(2 * np.pi * freq * t) * np.exp(-15 * t)
        return wave if isinstance(t, np.ndarray) else float(wave)
    return AudioClip(make_sound, duration=duration, fps=fps)

def combinar_audios(audio1, audio2, duracao):
    fps = audio1.fps
    def make_frame(t):
        import numpy as np
        t = np.array([t]) if isinstance(t, (float, int)) else t
        f1, f2 = audio1.get_frame(t), audio2.get_frame(t)
        f1 = f1.reshape(-1, 1) if f1.ndim == 1 else f1
        f2 = f2.reshape(-1, 1) if f2.ndim == 1 else f2
        mixed = np.clip(f1 + f2, -1, 1)
        return mixed.squeeze()
    return AudioClip(make_frame, duration=duracao, fps=fps)

def processar_video(input_path, output_path):
    fundo_path = os.path.expanduser("~/Desktop/InstaManual/EXEMPLOM4.MOV")
    fundo = VideoFileClip(fundo_path).without_audio()

    altura_resize = fundo.h * 0.45
    posicao_y = 1220

    video = VideoFileClip(input_path)
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

    # 🔹 Compactar: reduzir resolução máxima e aumentar CRF
    video_final = video_final.resize(height=720)

    video_final.write_videofile(
        output_path,
        codec='libx264',
        threads=4,
        audio_codec='aac',
        preset='slow',
        fps=30,
        ffmpeg_params=['-crf', '13']  # compactação maior
    )

    video.close()
    video_final.close()
    fundo.close()
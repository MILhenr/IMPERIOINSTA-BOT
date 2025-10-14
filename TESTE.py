import os
import cv2
import numpy as np
from scipy.io.wavfile import write as write_wav
from scipy.io import wavfile

def gerar_ding_audio(duration=0.3, freq=440, fs=44100):
    """
    Gera um som 'ding' simples e retorna como array numpy
    """
    t = np.linspace(0, duration, int(fs*duration), endpoint=False)
    wave = 0.1 * np.sin(2*np.pi*freq*t) * np.exp(-15*t)
    wave = np.clip(wave, -1, 1)
    wave_int16 = np.int16(wave * 32767)
    return wave_int16, 

def salvar_audio_ding(path='ding.wav'):
    ding_wave, fs = gerar_ding_audio()
    write_wav(path, fs, ding_wave)
    return path

def processar_video_cv2(input_path, output_path):
    """
    Processa vídeo usando OpenCV: redimensiona, centraliza e sobrepõe camada transparente
    """
    fundo_path = os.path.expanduser("~/Desktop/InstaManual/EXEMPLOM4.MOV")
    cap_fundo = cv2.VideoCapture(fundo_path)
    cap_video = cv2.VideoCapture(input_path)

    if not cap_fundo.isOpened() or not cap_video.isOpened():
        print("Erro ao abrir vídeos")
        return

    # Obter propriedades do vídeo
    fps = int(cap_video.get(cv2.CAP_PROP_FPS))
    width = int(cap_fundo.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap_fundo.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Criar VideoWriter para salvar
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Processar frame a frame
    while True:
        ret_fundo, frame_fundo = cap_fundo.read()
        ret_video, frame_video = cap_video.read()

        if not ret_fundo or not ret_video:
            break

        # Redimensionar vídeo para caber no fundo
        h_resize = int(height * 0.45)
        scale_ratio = h_resize / frame_video.shape[0]
        w_resize = int(frame_video.shape[1] * scale_ratio)
        frame_video_resized = cv2.resize(frame_video, (w_resize, h_resize))

        # Posicionar no centro horizontalmente e posicao_y vertical
        pos_y = 1220
        pos_x = (width - w_resize) // 2

        # Sobreposição simples
        overlay = frame_fundo.copy()
        overlay[pos_y:pos_y+h_resize, pos_x:pos_x+w_resize] = frame_video_resized

        # Camada transparente leve
        alpha = 0.02
        frame_final = cv2.addWeighted(overlay, alpha, frame_fundo, 1-alpha, 0)

        out.write(frame_final)

    cap_fundo.release()
    cap_video.release()
    out.release()
    cv2.destroyAllWindows()
    print("Vídeo processado com sucesso!")

# Exemplo de uso
if __name__ == "__main__":
    input_vid = 'entrada.mp4'
    output_vid = 'saida.mp4'
    salvar_audio_ding()  # salva arquivo ding.wav
    processar_video_cv2(input_vid, output_vid)
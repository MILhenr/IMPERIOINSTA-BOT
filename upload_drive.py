import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Escopos necessários para enviar arquivos para o Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def upload_to_drive(file_path, file_name):
    creds = None
    # arquivo de credenciais JSON
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    print(f'Arquivo enviado com sucesso! ID: {file.get("id")}')
    return f'https://drive.google.com/file/d/{file.get("id")}/view?usp=sharing'

# Exemplo de uso
video_path = 'saida.mp4'  # vídeo editado pelo bot
link = upload_to_drive(video_path, 'VideoEditado.mp4')
print("Link público:", link)
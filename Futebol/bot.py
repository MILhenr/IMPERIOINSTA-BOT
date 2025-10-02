import os
import importlib.util
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
)
from dotenv import load_dotenv

# Carrega token do .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("⚠️ BOT_TOKEN não encontrado no .env")
print("🔑 Token carregado com sucesso")

# Pasta onde estão os scripts de edição
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Dicionário para guardar vídeos temporários do usuário
user_videos = {}

# --------------------- FUNÇÕES ---------------------

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎥 Manda um vídeo que eu edito com o script que você escolher!"
    )
    print("▶️ /start executado")

# Recebe vídeo
async def receber_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    print(f"📥 Vídeo recebido de {user_id}")

    # Pega arquivo de vídeo
    video = update.message.video or update.message.document
    if not video:
        await update.message.reply_text("⚠️ Nenhum vídeo detectado.")
        print("❌ Nenhum vídeo encontrado")
        return

    # Baixa vídeo
    input_path = f"video_{user_id}.mp4"
    file = await video.get_file()
    await file.download_to_drive(input_path)
    user_videos[user_id] = input_path
    print(f"✅ Vídeo salvo em {input_path}")

    # Lista scripts disponíveis
    scripts = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".py") and f != "bot.py"]
    if not scripts:
        await update.message.reply_text("⚠️ Nenhum script de edição encontrado.")
        print("❌ Nenhum script de edição disponível")
        return

    # Cria teclado inline com scripts
    keyboard = [[InlineKeyboardButton(script, callback_data=script)] for script in scripts]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("⚙️ Escolhe o script para editar:", reply_markup=reply_markup)
    print(f"▶️ Opções enviadas para {user_id}: {scripts}")

# Escolha do script
async def escolher_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    script_name = query.data
    user_id = query.from_user.id

    if user_id not in user_videos:
        await query.edit_message_text("⚠️ Primeiro envie um vídeo.")
        return

    input_path = user_videos[user_id]
    output_path = f"editado_{user_id}.mp4"

    try:
        # Importa script dinamicamente
        module_name = script_name.replace(".py", "")
        spec = importlib.util.spec_from_file_location(module_name, os.path.join(SCRIPTS_DIR, script_name))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        print(f"▶️ Rodando script {script_name} para {user_id}")
        module.processar_video(input_path, output_path)

        await query.edit_message_text(f"✅ Script `{script_name}` finalizado. Enviando vídeo...")
        print(f"📤 Enviando vídeo finalizado {output_path}")

        # Envia vídeo editado como arquivo/documento (mantém qualidade)
        with open(output_path, "rb") as f:
            await query.message.reply_document(f, caption="✅ Vídeo editado com sucesso!")

    except Exception as e:
        await query.edit_message_text(f"❌ Erro no script `{script_name}`:\n{e}")
        print(f"❌ Erro no script {script_name}: {e}")

    finally:
        # Limpa arquivos temporários
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        user_videos.pop(user_id, None)
        print(f"🗑️ Arquivos temporários removidos para {user_id}")

# --------------------- MAIN ---------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    # Pega vídeos enviados como video ou documento
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, receber_video))
    app.add_handler(CallbackQueryHandler(escolher_script))

    print("🚀 Bot iniciado")
    app.run_polling()

if __name__ == "__main__":
    main()
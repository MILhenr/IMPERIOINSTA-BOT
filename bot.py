import os
import importlib.util
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv
from upload_drive import upload_to_drive  # <-- import do upload para Drive

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Pasta onde estão os scripts de edição
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Guarda os vídeos temporários enviados pelos usuários
user_videos = {}

# ---- Comandos do bot ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎥 Mande um vídeo que eu vou editar usando os scripts disponíveis!"
    )

# ---- Recebe vídeo e mostra opções ----
async def receber_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    file = await update.message.video.get_file()
    input_path = f"video_{user_id}.mp4"
    await file.download_to_drive(input_path)
    user_videos[user_id] = input_path

    # Lista scripts disponíveis
    scripts = [
        f for f in os.listdir(SCRIPTS_DIR)
        if f.endswith(".py") and f.startswith("codigo")
    ]

    if not scripts:
        await update.message.reply_text("⚠️ Nenhum script de edição encontrado.")
        return

    keyboard = [[InlineKeyboardButton(script, callback_data=script)] for script in scripts]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ Escolha o script para editar:", reply_markup=reply_markup)

# ---- Escolhe o script e processa o vídeo ----
async def escolher_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    script_name = query.data
    user_id = query.from_user.id

    if user_id not in user_videos:
        await query.edit_message_text("⚠️ Primeiro envie um vídeo.")
        return

    input_path = user_videos[user_id]
    output_path = f"saida_{user_id}.mp4"

    try:
        # Carrega o script dinamicamente
        module_name = script_name.replace(".py", "")
        spec = importlib.util.spec_from_file_location(module_name, os.path.join(SCRIPTS_DIR, script_name))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Processa o vídeo
        module.processar_video(input_path, output_path)

        # Upload para Google Drive
        link = upload_to_drive(output_path, f"VideoEditado_{user_id}.mp4")

        await query.edit_message_text(f"✅ Vídeo editado com sucesso!\n📂 Link no Drive: {link}")

    except Exception as e:
        await query.edit_message_text(f"❌ Erro no script `{script_name}`:\n{e}")

    finally:
        # Limpa arquivos temporários
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

# ---- MAIN ----
def main():
    if not BOT_TOKEN:
        raise ValueError("⚠️ BOT_TOKEN não encontrado no .env")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, receber_video))
    app.add_handler(CallbackQueryHandler(escolher_script))
    app.run_polling()

if __name__ == "__main__":
    main()
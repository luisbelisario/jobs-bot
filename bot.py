import os
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler
from telegram.error import TelegramError

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def start(update: Update, context):
    update.message.reply_text("Bot ativo! Use /test para receber uma mensagem de teste.")

def send_test_message():
    try:
        bot = Bot(token=TOKEN)
        bot.send_message(
            chat_id=CHAT_ID,
            text="EU AMO A NATASSIA E O BABYZINHO",
            parse_mode="Markdown"
        )
    except TelegramError as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("Token do bot não configurado no arquivo .env!")
    if not CHAT_ID:
        raise ValueError("Chat ID não configurado no arquivo .env!")

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("test", lambda u, c: send_test_message()))
    
    print("Bot rodando... Pressione Ctrl+C para parar.")
    updater.start_polling()
    updater.idle()
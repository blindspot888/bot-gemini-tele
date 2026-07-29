import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 1. Ambil Kunci Rahasia dari Environment Variables (Render)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo Bro! Bot Gemini siap bantu kamu. Langsung ketik pertanyaanmu!")

# Fungsi Utama untuk Menjawab Chat Teks
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Efek 'typing...' di Telegram biar kelihatan lagi mikir
    await update.message.chat.send_action(action="typing")
    
    try:
        # Minta jawaban ke Gemini
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Duh, ada error bro: {str(e)}")

# Jalankan Bot
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot Gemini sukses jalan!")
    app.run_polling()

if __name__ == "__main__":
    main()

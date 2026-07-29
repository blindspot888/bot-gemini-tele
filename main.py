import os
import json
import asyncio
from telegram import Bot
import google.generativeai as genai

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OFFSET_FILE = "offset.json"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def load_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE, "r") as f:
            return json.load(f).get("offset", 0)
    return 0

def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        json.dump({"offset": offset}, f)

async def ask_gemini(text: str) -> str:
    try:
        response = model.generate_content(text)
        return response.text
    except Exception as e:
        return f"Duh, ada error bro: {str(e)}"

async def main():
    offset = load_offset()
    updates = await bot.get_updates(offset=offset, timeout=10)

    for update in updates:
        offset = update.update_id + 1

        if update.message and update.message.text:
            chat_id = update.message.chat_id
            text = update.message.text

            if text.startswith("/start"):
                reply = "Halo Bro! Bot Gemini siap bantu kamu. Langsung ketik pertanyaanmu!"
            else:
                reply = await ask_gemini(text)

            await bot.send_message(chat_id=chat_id, text=reply)

    save_offset(offset)
    print(f"Selesai. Offset terakhir: {offset}")

if __name__ == "__main__":
    asyncio.run(main())

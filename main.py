import os
import json
import asyncio
from io import BytesIO
from telegram import Bot
import google.generativeai as genai

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OFFSET_FILE = "offset.json"

genai.configure(api_key=GEMINI_API_KEY)

chat_model = genai.GenerativeModel("gemini-flash-latest")
image_gen_model = genai.GenerativeModel("gemini-3.1-flash-image")

bot = Bot(token=TELEGRAM_BOT_TOKEN)


def load_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE, "r") as f:
            return json.load(f).get("offset", 0)
    return 0


def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        json.dump({"offset": offset}, f)


async def ask_gemini_text(text: str) -> str:
    try:
        response = chat_model.generate_content(text)
        return response.text
    except Exception as e:
        return f"Duh, ada error bro: {str(e)}"


async def ask_gemini_image_understanding(image_bytes: bytes, caption: str) -> str:
    try:
        image_part = {"mime_type": "image/jpeg", "data": image_bytes}
        prompt = caption if caption else "Deskripsikan gambar ini."
        response = chat_model.generate_content([prompt, image_part])
        return response.text
    except Exception as e:
        return f"Duh, ada error bro: {str(e)}"


async def generate_image(prompt: str):
    """Return (image_bytes or None, error_text or None)"""
    try:
        response = image_gen_model.generate_content(prompt)
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data is not None:
                return part.inline_data.data, None
        return None, "Gemini gak ngembaliin gambar, coba prompt lain bro."
    except Exception as e:
        return None, f"Duh, ada error bro: {str(e)}"


async def handle_text(chat_id: int, text: str):
    if text.startswith("/start"):
        reply = (
            "Halo Bro! Bot Gemini siap bantu kamu.\n\n"
            "- Ketik apa aja buat ngobrol\n"
            "- Kirim foto (+ caption opsional) buat dianalisa\n"
            "- Ketik /gambar <deskripsi> buat bikin gambar"
        )
        await bot.send_message(chat_id=chat_id, text=reply)

    elif text.startswith("/gambar"):
        prompt = text.replace("/gambar", "", 1).strip()
        if not prompt:
            await bot.send_message(chat_id=chat_id, text="Kasih deskripsi gambarnya bro, contoh: /gambar kucing astronot")
            return

        await bot.send_chat_action(chat_id=chat_id, action="upload_photo")
        image_bytes, error = await generate_image(prompt)
        if error:
            await bot.send_message(chat_id=chat_id, text=error)
        else:
            await bot.send_photo(chat_id=chat_id, photo=BytesIO(image_bytes))

    else:
        reply = await ask_gemini_text(text)
        await bot.send_message(chat_id=chat_id, text=reply)


async def handle_photo(chat_id: int, photo, caption: str):
    file = await bot.get_file(photo.file_id)
    buf = BytesIO()
    await file.download_to_memory(out=buf)
    image_bytes = buf.getvalue()

    reply = await ask_gemini_image_understanding(image_bytes, caption)
    await bot.send_message(chat_id=chat_id, text=reply)


async def main():
    offset = load_offset()
    updates = await bot.get_updates(offset=offset, timeout=10)

    for update in updates:
        offset = update.update_id + 1

        if not update.message:
            continue

        chat_id = update.message.chat_id

        if update.message.photo:
            caption = update.message.caption or ""
            await handle_photo(chat_id, update.message.photo[-1], caption)

        elif update.message.text:
            await handle_text(chat_id, update.message.text)

    save_offset(offset)
    print(f"Selesai. Offset terakhir: {offset}")


if __name__ == "__main__":
    asyncio.run(main())

import os
from pyrogram import Client
from bot.config import TOKEN, API_ID, API_HASH
import logging
import asyncio

logger = logging.getLogger(__name__)

async def send_large_file(user_id, file_path):
    file_size = os.path.getsize(file_path) / (1024 * 1024)
    logger.info(f"Fayl yuborilmoqda: {file_path}, Hajmi: {file_size} MB, User ID: {user_id}")

    if file_size > 2000:
        return "❌ Fayl hajmi 2GB dan oshib ketdi!"

    app = Client("bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            await app.start()
            if file_path.endswith(".mp4"):
                await app.send_video(user_id, file_path, caption="✅ Video yuklandi!")
            elif file_path.endswith(".mp3"):
                await app.send_audio(user_id, file_path, caption="🎵 Audio yuklandi!")
            else:
                await app.send_document(user_id, file_path, caption="📂 Fayl yuklandi!")
            return "🎉 Xizmatdan foydalanganingiz uchun rahmat!\n\n/start buyrug‘i orqali yana videolar yuklab olishingiz mumkin! 🚀"
        except Exception as e:
            logger.error(f"Fayl yuborishda xato (Urinish {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return f"⚠️ Xatolik yuz berdi: {str(e)}"
        finally:
            try:
                await app.stop()
            except Exception as e:
                logger.warning(f"Clientni yopishda xato: {e}")
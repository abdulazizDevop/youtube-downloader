import bot.keyboards as kb
import yt_dlp as ytd
import os
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from bot.uploader import send_large_file

rt = Router()
user_links = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@rt.message(F.text)
async def getlink(message: Message):
    url = message.text
    user_links[message.from_user.id] = url

    if "youtube.com" in url or "youtu.be" in url:
        await message.answer("🎥 Yuklab olish formatini tanlang:", reply_markup=kb.chBtn)
    elif "instagram.com" in url or "tiktok.com" in url:
        await message.answer("📥 Yuklab olinmoqda... 🕑 Biroz kuting")
        await download_social_media_video(message, url)
    else:
        await message.answer("❌ Noto‘g‘ri URL! Faqat YouTube, Instagram va TikTok linklarini yuboring.")

async def download_social_media_video(message: Message, url: str):
    options = {
        'outtmpl': 'output/video/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
    }

    try:
        with ytd.YoutubeDL(options) as ytdl:
            result = ytdl.extract_info(url, download=True)

            if "entries" in result:
                files = []
                for entry in result["entries"]:
                    file_path = f"output/video/{entry['id']}.mp4"
                    if os.path.exists(file_path):
                        files.append(file_path)
            else:
                file_path = f"output/video/{result['id']}.mp4"
                files = [file_path] if os.path.exists(file_path) else []

            if not files:
                if 'image' in result:
                    image_url = result['image']
                    image_path = f"output/images/{result['id']}.jpg"
                    await download_image(image_url, image_path)
                    await message.answer_photo(FSInputFile(image_path), caption="✅ Rasm yuklab olindi!")
                    os.remove(image_path)
                    return

                await message.answer("❌ Yuklab olishda xatolik yuz berdi.")
                return

            for file_path in files:
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                logger.info(f"Fayl hajmi: {file_size} MB")

                if file_size <= 50:
                    await message.answer_video(FSInputFile(file_path), caption="✅ Video yuklab olindi!")
                else:
                    response = await send_large_file(message.from_user.id, file_path)
                    await message.answer(response)

                await asyncio.sleep(2)
                os.remove(file_path)

    except Exception as e:
        logger.error(f"Yuklab olishda xatolik: {e}")
        await message.answer(f"⚠️ Yuklab olishda xatolik yuz berdi: {str(e)}")

async def download_image(image_url, image_path):
    import requests
    response = requests.get(image_url)
    with open(image_path, 'wb') as file:
        file.write(response.content)


async def download_youtube_video(url, resolution):
    options = {
        'format': f'bestvideo[height<={resolution}]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'output/video/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'overwrites': True,
    }
    try:
        with ytd.YoutubeDL(options) as ytdl:
            result = ytdl.extract_info(url, download=True)
            file_path = f"output/video/{result['id']}.mp4"
            if os.path.exists(file_path):
                await asyncio.sleep(1)
                return file_path
            return None
    except Exception as e:
        logger.error(f"Video yuklashda xato: {e}")
        return None

@rt.callback_query(F.data.in_(["1080", "720", "360"]))
async def download_video(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_links:
        await callback.message.answer("❌ Iltimos, avval video linkini yuboring!")
        return

    link = user_links[user_id]
    resolution = callback.data
    await callback.message.answer("📥 Yuklab olinmoqda...\n\n🕑 Bir necha daqiqa kuting")

    file_path = await download_youtube_video(link, resolution)

    if file_path and os.path.exists(file_path):
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        logger.info(f"Fayl hajmi: {file_size} MB")

        if file_size <= 50:
            try:
                await callback.message.answer_video(FSInputFile(file_path), caption="✅ Video yuklab olindi!")
            except Exception as e:
                logger.error(f"Kichik faylni yuborishda xato: {e}")
                await callback.message.answer("⚠️ Video yuklashda xatolik yuz berdi!")
        else:
            try:
                response = await send_large_file(callback.from_user.id, file_path)
                await callback.message.answer(response)
            except Exception as e:
                logger.error(f"Katta faylni yuborishda xato: {e}")
                await callback.message.answer(f"⚠️ Video yuklashda xatolik yuz berdi: {str(e)}")

        await asyncio.sleep(2)
        os.remove(file_path)
    else:
        await callback.message.answer("❌ Yuklab olishda xatolik yuz berdi. Iltimos, boshqa linkni sinab ko'ring.")

async def download_youtube_audio(url):
    options = {
        'format': 'bestaudio/best',
        'outtmpl': 'output/mp3/%(id)s.%(ext)s',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with ytd.YoutubeDL(options) as ytdl:
        result = ytdl.extract_info(url, download=True)
        file_path = f"output/mp3/{result['id']}.mp3"

        if not os.path.exists(file_path):
            return None

        return file_path

@rt.callback_query(F.data == "mp3")
async def download_audio(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_links:
        await callback.message.answer("❌ Iltimos, avval video linkini yuboring!")
        return

    link = user_links[user_id]
    await callback.message.answer("🎧 Audio yuklab olinmoqda...\n🕑 Biroz kuting")

    file_path = await download_youtube_audio(link)

    if file_path and os.path.exists(file_path):
        file_size = os.path.getsize(file_path) / (1024 * 1024)

        if file_size <= 50:
            await callback.message.answer_audio(FSInputFile(file_path), caption="✅ Audio yuklab olindi!")
        else:
            try:
                response = await send_large_file(callback.from_user.id, file_path)
                await callback.message.answer(response)
            except Exception as e:
                await callback.message.answer("⚠️ Audio yuklashda xatolik yuz berdi!")

        await asyncio.sleep(2)
        os.remove(file_path)
    else:
        await callback.message.answer("❌ Yuklab olishda xatolik yuz berdi. Iltimos, boshqa linkni sinab ko'ring.")
# bot/handler.py
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

@router.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(f"👋 Salom, {message.from_user.full_name}!\n\n🎥 Menga YouTube, Instagram va TikTok link yuboring, men sizga video yoki audio yuklab beraman!")
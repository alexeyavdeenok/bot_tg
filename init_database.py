from database2 import db
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
from aiogram import Bot

async def init_db():
    await db.connect()

scheduler = AsyncIOScheduler()
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ZZ = os.getenv('ZZ')
bot = Bot(token=BOT_TOKEN)

async def send_reminder(user_id, message):
    try:
        await bot.send_message(user_id, f"Напоминание: {message}")
    except Exception as e:
        print(f"Ошибка: {e}")
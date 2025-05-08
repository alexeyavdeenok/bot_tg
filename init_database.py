from database2 import db
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
from aiogram import Bot
from logger import logger

async def init_db():
    await db.connect()

scheduler = AsyncIOScheduler()
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ZZ = os.getenv('ZZ')
bot = Bot(token=BOT_TOKEN)

async def send_reminder(user_id, message):
    try:
        if await db.get_reminders_mode(user_id) == 1:
            await bot.send_message(user_id, f"Напоминание: {message}")
            logger.info(f"Напоминание успешно отправлено пользователю {user_id}: {message}")
        else:
            logger.info(f"Напоминание для пользователя {user_id} не отправлено, так как режим напоминаний отключен")
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминания пользователю {user_id}: {e}", exc_info=True)
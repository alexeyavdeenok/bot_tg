import aiosqlite
import asyncio
from logger import logger

class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        self.connection = None

    async def connect(self):
        """Устанавливает соединение с базой данных."""
        if self.connection is None:
            self.connection = await aiosqlite.connect(self.db_path)
            logger.info('Подключение к базе данных')
            try:
                await self._initialize_tables()
            except Exception as e:
                logger.error(f"Ошибка при создании таблиц: {e}", exc_info=True)

    async def disconnect(self):
        """Закрывает соединение с базой данных."""
        if self.connection:
            await self.connection.close()
            self.connection = None
            logger.info('Отключение от базы данных')

    async def _initialize_tables(self):
        """Создаёт таблицы, если их нет."""
        async with self.connection.cursor() as cursor:
            # Таблица пользователей
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT
                )
            """)

            # Таблица расписания
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    day TEXT,
                    subject TEXT,
                    time TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)

            # Таблица TODO-листа
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS todo_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task TEXT,
                    deadline TEXT,
                    is_completed BOOLEAN DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)

            # Таблица мероприятий
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    date TEXT,
                    time TEXT,
                    reminder_frequency TEXT,
                    is_periodic BOOLEAN DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)

            await self.connection.commit()

    async def add_user(self, user_id: int, username: str):
        """Добавляет нового пользователя."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username),
            )
            logger.info('Пользователь добавлен')
            await self.connection.commit()

    async def get_user(self, user_id: int):
        """Получает информацию о пользователе по user_id."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            )
            return await cursor.fetchone()

    async def add_task(self, user_id: int, task: str, deadline: str):
        """Добавляет задачу в TODO-лист."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO todo_list (user_id, task, deadline) VALUES (?, ?, ?)",
                (user_id, task, deadline),
            )
            await self.connection.commit()

    async def get_tasks(self, user_id: int):
        """Получает список задач для пользователя."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM todo_list WHERE user_id = ?",
                (user_id,),
            )
            return await cursor.fetchall()

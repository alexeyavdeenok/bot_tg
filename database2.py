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
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedule_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    title TEXT,
                    is_important BOOLEAN DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)
            await cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                job_name TEXT,
                trigger_type INTEGER,
                trigger_time TEXT,
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

    async def add_task(self, user_id: int, task: str, deadline: str, priority: int = 1):
        """Добавляет задачу в TODO-лист и возвращает сгенерированный ID задачи."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO todo_list (user_id, task, deadline, priority) VALUES (?, ?, ?, ?)",
                (user_id, task, deadline, priority),
            )
            await self.connection.commit()
            task_id = cursor.lastrowid  # Получаем сгенерированный ID
            logger.info(f"Задача '{task}' добавлена для пользователя {user_id} с ID {task_id} и приоритетом {priority}")
            return task_id

    async def get_tasks(self, user_id: int):
        """Получает список задач для пользователя с их приоритетами."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT id, user_id, task, deadline, priority, is_completed FROM todo_list WHERE user_id = ?",
                (user_id,),
            )
            return await cursor.fetchall()
    
    async def update_task_priority(self, task_id: int, new_priority: int):
        """Обновляет приоритет задачи."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "UPDATE todo_list SET priority = ? WHERE id = ?",
                (new_priority, task_id),
            )
            await self.connection.commit()
            logger.info(f"Приоритет задачи с ID {task_id} обновлен на {new_priority}")

    async def update_task_deadline(self, task_id: int, new_deadline: str):
        """Обновляет дедлайн задачи."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "UPDATE todo_list SET deadline = ? WHERE id = ?",
                (new_deadline, task_id),
            )
            await self.connection.commit()
            logger.info(f"Дедлайн задачи с ID {task_id} обновлен на {new_deadline}")

    async def delete_task(self, task_id: int):
        """Удаляет задачу по её ID."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM todo_list WHERE id = ?",
                (task_id,),
            )
            await self.connection.commit()
            logger.info(f"Задача с ID {task_id} удалена")
    
    async def add_schedule_event(self, user_id: int, date: str, start_time: str, end_time: str, title: str, is_important: bool = True):
        """Добавляет новое событие в расписание."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO schedule_events (user_id, date, start_time, end_time, title, is_important) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, date, start_time, end_time, title, int(is_important)),
            )
            await self.connection.commit()
            event_id = cursor.lastrowid 
            logger.info(f"Событие '{title}' добавлено для пользователя {user_id}")
            return event_id

    async def get_schedule_events(self, user_id: int, date: str = None):
        """Получает все события пользователя. Если указана дата, возвращает события за эту дату."""
        async with self.connection.cursor() as cursor:
            if date:
                await cursor.execute(
                    "SELECT event_id, date, start_time, end_time, title, is_important FROM schedule_events WHERE user_id = ? AND date = ?",
                    (user_id, date),
                )
            else:
                await cursor.execute(
                    "SELECT event_id, date, start_time, end_time, title, is_important FROM schedule_events WHERE user_id = ?",
                    (user_id,),
                )
            return await cursor.fetchall()

    async def delete_schedule_event(self, event_id: int):
        """Удаляет событие по его ID."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM schedule_events WHERE event_id = ?",
                (event_id,),
            )
            await self.connection.commit()
            logger.info(f"Событие с ID {event_id} удалено")
    
    async def update_event_important(self, event_id: int, is_important: bool):
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "UPDATE schedule_events SET is_important = ? WHERE event_id = ?",
                (int(is_important), event_id),
            )
            await self.connection.commit()
    
    async def add_reminder(self, user_id: int, job_name: str, trigger_type: int, trigger_time: str) -> int:
        """Добавляет новое напоминание и возвращает сгенерированный job_id."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO reminders (user_id, job_name, trigger_type, trigger_time) VALUES (?, ?, ?, ?)",
                (user_id, job_name, trigger_type, trigger_time),
            )
            await self.connection.commit()
            job_id = cursor.lastrowid
            logger.info(f"Напоминание '{job_name}' добавлено для пользователя {user_id} с ID {job_id}")
            return job_id
        
    async def delete_reminder(self, job_id: int):
        """Удаляет напоминание по его job_id."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM reminders WHERE job_id = ?",
                (job_id,),
            )
            await self.connection.commit()
            logger.info(f"Напоминание с ID {job_id} удалено")
    
    async def get_reminders_by_user(self, user_id: int):
        """Получает все напоминания для пользователя."""
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT job_id, user_id, job_name, trigger_type, trigger_time FROM reminders WHERE user_id = ?",
                (user_id,),
            )
            return await cursor.fetchall()
        
    async def get_all_users(self):
        """Получает всех пользователей из таблицы users.

        Returns:
            list: Список кортежей, где каждый кортеж содержит данные пользователя (user_id, username).
                Пустой список, если произошла ошибка или пользователей нет.
        Raises:
            ConnectionError: Если соединение с базой данных не установлено.
        """
        if self.connection is None:
            raise ConnectionError("Соединение с базой данных не установлено.")
        
        async with self.connection.cursor() as cursor:
            try:
                await cursor.execute("SELECT user_id FROM users")
                users = await cursor.fetchall()
                return [i[0] for i in users]
            except Exception as e:
                logger.error(f"Ошибка при получении пользователей: {e}", exc_info=True)
                return []

async def get_table_structure():
    db_path = "bot.db"  # Укажите путь к вашей базе данных
    async with aiosqlite.connect(db_path) as db:
        # Проверяем существование таблицы
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='todo_list'")
        table_exists = await cursor.fetchone()
        if not table_exists:
            print("Таблица todo_list не существует в базе данных.")
            return

        # Получаем структуру таблицы
        cursor = await db.execute("PRAGMA table_info(todo_list);")
        columns = await cursor.fetchall()

        print("Структура таблицы todo_list:")
        print("-" * 40)
        print(f"{'Имя':<15}{'Тип':<15}{'PK':<5}")
        print("-" * 40)
        for column in columns:
            cid, name, type, notnull, dflt_value, pk = column
            print(f"{name:<15}{type:<15}{'Да' if pk else '':<5}")


        
db = Database()

if __name__ == "__main__":
    asyncio.run(get_table_structure())
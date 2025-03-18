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

    async def disconnect(self):
        """Закрывает соединение с базой данных."""
        if self.connection:
            await self.connection.close()
            self.connection = None
            logger.info('Отключение от базы данных')

    async def show_todo_list_structure(self):
        """Выводит структуру таблицы todo_list."""
        async with self.connection.cursor() as cursor:
            await cursor.execute("PRAGMA table_info(todo_list);")
            columns = await cursor.fetchall()
            
            print("Структура таблицы 'todo_list':")
            print(f"{'Имя':<15} {'Тип':<15} {'Не пусто':<8} {'По умолчанию':<15} {'PK':<5}")
            print("-" * 70)
            
            for column in columns:
                cid, name, type_, notnull, dflt_value, pk = column
                # Обработка значения по умолчанию
                dflt_value_str = str(dflt_value) if dflt_value is not None else 'None'
                print(f"{name:<15} {type_:<15} {'да' if notnull else 'нет':<8} {dflt_value_str:<15} {'да' if pk else 'нет':<5}")

if __name__ == '__main__':
    db = Database()
    asyncio.run(db.connect())
    asyncio.run(db.show_todo_list_structure())
    asyncio.run(db.disconnect())
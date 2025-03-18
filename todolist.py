import database
import asyncio
from datetime import date, timedelta

priority_dict = {1: '🟨', 2: '🟧', 3: '🟥'}

class Todolist:
    def __init__(self, title,database, show_completed=False):
        self.title = title
        self.db = database
        self.tasks = []
        self.show_completed = show_completed
        self.completed_tasks = []
    
    async def load_tasks(self, user_id: int):
        """Загружает задачи из базы данных для указанного пользователя."""
        tasks_data = await self.db.get_tasks(user_id)
        self.tasks = []
        for task_data in tasks_data:
            task_id, user_id, task, deadline, priority, is_completed = task_data
            # Используем статический метод parse_date для получения объекта даты
            deadline_date, show_year = self.parse_date(deadline)
            task_obj = Task(
                title=task,
                deadline=deadline_date,
                priority=priority,
                show_year=show_year,
                completed=is_completed,
                task_id=task_id
            )
            self.tasks.append(task_obj)
        self.tasks.sort(key=lambda x: (x.deadline, -x.priority))
    
    def add_task(self, deadline_date, title, priority):
        deadline, show_year = self.parse_date(deadline_date)
        task = Task(title, deadline, priority, show_year)
        self.tasks.append(task)
        self.tasks.sort(key=lambda x: (x.deadline, -x.priority))
    
    def complete_task(self, index):
        self.tasks[index].complete()
        self.completed_tasks.append(self.tasks[index])
        self.tasks.pop(index)
    

    @staticmethod
    def parse_date(date_str: str) -> tuple[date, bool]:
        parts = date_str.split('.')
        
        if len(parts) not in (2, 3):
            raise ValueError("Неверный формат даты. Ожидается ДД.ММ или ДД.ММ.ГГГГ.")
        
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2]) if len(parts) == 3 else date.today().year
            
        return (date(year, month, day), len(parts) == 3)
        



class Task:
    def __init__(self, title, deadline, priority, show_year, completed=False, task_id=None):
        self.title = title
        self.deadline = deadline
        self.task_id = task_id
        self.priority = priority
        self.completed = completed
        self.show_year = show_year

    def __str__(self):
        if self.show_year:
            return f'{priority_dict[self.priority]} {self.dedline.strftime("%d.%m.%Y")} {self.title} '
        return f'{priority_dict[self.priority]} {self.deadline.strftime("%d.%m")} {self.title} '
    
    def complete(self):
        self.completed = True

    def change_priority(self, new_priority):
        self.priority = new_priority
    
    def change_deadline(self, new_deadline):
        self.deadline = new_deadline
    
    def get_date(self):
        if self.show_year:
            return self.deadline.strftime("%d.%m.%Y")
        return self.deadline.strftime("%d.%m")
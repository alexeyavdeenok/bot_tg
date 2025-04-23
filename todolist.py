from database import *
import asyncio
from datetime import date, timedelta
from container import measure_execution_time

priority_dict = {1: '🟨', 2: '🟧', 3: '🟥'}

class Todolist:
    def __init__(self, title, database, show_completed):
        self.title = title
        self.db = database
        self.tasks = []
        self.show_completed = show_completed
        self.completed_tasks = []
        self.current_task = None
    
    @measure_execution_time
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
    
    async def add_task(self, title, deadline_date, priority, user_id=None):
        deadline, show_year = self.parse_date(deadline_date)
        if user_id is not None:
            if show_year:
                deadline_str = deadline.strftime("%d.%m.%Y")
            else:
                deadline_str = deadline.strftime("%d.%m")
            task = Task(title, deadline, priority, show_year, task_id=await self.db.add_task(user_id, title, deadline_str, priority))
        else:
            task = Task(title, deadline, priority, show_year)
        self.current_task = task
        self.tasks.append(task)
        self.tasks.sort(key=lambda x: (x.deadline, -x.priority))
    
    def complete_task(self, index):
        self.tasks[index].complete()
        self.completed_tasks.append(self.tasks[index])
        self.tasks.pop(index)
        if len(self.completed_tasks) > 5:
            self.completed_tasks.pop(0)
    
    def delete_task(self):
        self.tasks.pop(self.tasks.index(self.current_task))
    
    def __str__(self):
        if not self.show_completed:
            return f'{self.title}\n{'~' * 25}\n' + '\n'.join([str(i) + '- ' +self.get_deadline(i) for i in self.tasks])
        else:
            return f'{self.title}\n{'~' * 25}\n' + '\n'.join([str(i) + '- ' +self.get_deadline(i) for i in self.tasks]) \
            + f'\n{'=' * 25}\nВыполнено\n{'~' * 25}\n' + '\n'.join([str(i) + '- ' +self.get_deadline(i) for i in self.completed_tasks])
    
    def get_deadline(self, task):
        delta = task.deadline - date.today()
        days_delta = delta.days
        if days_delta == 0:
            return "Сегодня"
        elif days_delta == 1:
            return "1 день"
        elif 2 <= days_delta <= 4:
            return f"{days_delta} дня"
        elif days_delta < 0:
            return f'{abs(days_delta)} дней назад'
        else:
            return f"{days_delta} дней"
        
    def set_current_task(self, index):
        self.current_task = self.tasks[index]

    def set_current_task_by_id(self, task_id):
        self.current_task = next((task for task in self.tasks if task.task_id == task_id), None)
    
    def change_deadline(self, new_deadline):
        self.current_task.change_deadline(new_deadline)
        self.tasks.sort(key=lambda x: (x.deadline, -x.priority))

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
            return f'{priority_dict[self.priority]} {self.deadline.strftime("%d.%m.%Y")} {self.title} '
        return f'{priority_dict[self.priority]} {self.deadline.strftime("%d.%m")} {self.title} '
    
    def set_task_id(self, task_id):
        self.task_id = task_id
    
    def complete(self):
        self.completed = True

    def change_priority(self, new_priority):
        self.priority = new_priority
    
    def change_deadline(self, new_deadline):
        self.deadline, self.show_year = Todolist.parse_date(new_deadline)
    
    def get_date(self):
        if self.show_year:
            return self.deadline.strftime("%d.%m.%Y")
        return self.deadline.strftime("%d.%m")
class Container:
    def __init__(self):
        self.user_schedules = {}
        self.user_todolist = {}
        self.show_complete = False
        self.user_remindes = {}
        self.reminders_on = True

    def get_schedule(self):
        return self.user_schedules
    
    def get_todolist(self):
        return self.user_todolist
    
    def get_show_complete(self):
        return self.show_complete
    
    def get_remindes(self):
        return self.user_remindes
    
    def get_reminders_mode(self):
        return self.reminders_on

cont = Container()

import time
from functools import wraps

def measure_execution_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # Запуск таймера
        result = func(*args, **kwargs)    # Выполнение функции
        end_time = time.perf_counter()    # Остановка таймера
        execution_time = end_time - start_time  # Время выполнения (в секундах)
        print(f"Функция {func.__name__} выполнена за {execution_time:.10f} секунд")
        return result
    return wrapper
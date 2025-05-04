from datetime import datetime
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from logger import logger
from init_database import *

day_convert = {
    "понедельник": 0, "пн": 0,
    "вторник": 1, "вт": 1,
    "среда": 2, "ср": 2,
    "четверг": 3, "чт": 3,
    "пятница": 4, "пт": 4,
    "суббота": 5, "сб": 5,
    "воскресенье": 6, "вс": 6}

class JobList:
    def __init__(self, user_id, db):
        self.user_id = user_id
        self.db = db
        self.job_list = []

    async def load_reminders(self):
        """Загружает напоминания из базы данных и добавляет их в список."""
        reminders_data = await self.db.get_reminders_by_user(self.user_id)
        for reminder_data in reminders_data:
            job_id, user_id, job_name, trigger_type, trigger_time = reminder_data
            try:
                job = Job(job_name, trigger_type, trigger_time)
                job.job_id = job_id  # Сохраняем job_id для futuro удаления или обновления
                self.job_list.append(job)
            except ValueError as e:
                logger.error(f"Ошибка при загрузке напоминания {job_name}: {e}")

    async def add_job(self, job_name, trigger_type, trigger_time):
        job = Job(job_name, trigger_type, trigger_time)
        job.job_id = await self.db.add_reminder(self.user_id, job.job_name, trigger_type, trigger_time)
        self.job_list.append(job)
        scheduler.add_job(
                send_reminder,
                trigger=job.trigger,  # Триггер задачи (например, дата или интервал)
                args=[self.user_id, job.job_name],  # Аргументы для функции напоминания
                id=str(job.job_id),  # Уникальный ID задачи
                replace_existing=True  # Заменяем задачу, если она уже существует
            )

    async def delete_job(self, index):
        j = self.job_list[index].job_id
        await self.db.delete_reminder(self.job_list[index].job_id)
        self.job_list.pop(index)
        scheduler.remove_job(str(j))

    async def import_job_from_schedule(self, event, date_str):
        event_time = event.start
        event_date = date_str.strftime("%d.%m.%Y")
        event_for_job = event_time + " " + event_date
        job = Job(event.title, 3, event_for_job)
        await self.add_job(job.job_name, 3, event_for_job)

    async def import_job_from_todolist(self, task):
        job = Job(task.title, 3, task.deadline.strftime("%d.%m.%Y"))
        await self.add_job(task.title, 3, task.deadline.strftime("%d.%m.%Y"))

    def __str__(self):
        return f'Напоминания\n{'~' * 25}\n' + '\n'.join(str(i) for i in self.job_list)
        

class Job:
    def __init__(self, job_name, trigger_type, trigger_time):
        self.job_name = job_name
        self.job_id = None
        self.text_job = None
        self.str_trgger_time = None
        self.set_trigger(trigger_type, trigger_time)

    def __str__(self):
        return f"{self.job_name} | {self.str_trgger_time}"

    def _parse_days(self, days_str):
        parts = days_str.split(',')
        result = []
        for part in parts:
            part = part.strip()
            if '-' in part:
                start_str, end_str = part.split('-')
                start = self._day_to_number(start_str.strip())
                end = self._day_to_number(end_str.strip())
                # CronTrigger автоматически обрабатывает cases like 5-0 как 5-6,0-0
                result.append(f"{start}-{end}")
            else:
                result.append(str(self._day_to_number(part)))
        return ','.join(result)

    def _day_to_number(self, day_name):
        """Преобразовать название дня в число (0-6)"""
        day_name_lower = day_name.lower()
        if day_name_lower not in day_convert:
            raise ValueError(f"Неверное название дня: '{day_name}'")
        return day_convert[day_name_lower]

    def set_trigger(self, trigger_type, trigger_time):
        """Устанавливает триггер APScheduler на основе типа и времени."""

        # Валидация типа триггера в начале
        try:
            trigger_type = int(trigger_type)
            if trigger_type not in [1, 2, 3]:
                 raise ValueError("Неизвестный тип") # Внутреннее сообщение, будет перехвачено
        except (ValueError, TypeError):
             # Выбрасываем более дружественное сообщение для пользователя
             raise ValueError(f"Неверный тип триггера: '{trigger_type}'. Ожидается число 1, 2 или 3.")


        if trigger_type == 2:  # CronTrigger (дни недели/диапазон время ЧЧ:ММ)
            try:
                # Пробуем разделить строку. Ожидаем 2 части: дни и время
                parts = trigger_time.strip().rsplit(' ', 1)
                if len(parts) != 2:
                     raise ValueError(f"Неверный формат. Ожидается 'дни время', например 'понедельник 10:30'.")

                days_str, time_str = parts

                # Парсинг времени
                try:
                    dt_time = datetime.strptime(time_str, "%H:%M")
                    hour = dt_time.hour
                    minute = dt_time.minute
                except ValueError:
                    raise ValueError(f"Неверный формат времени в Cron триггере: '{time_str}'. Ожидается ЧЧ:ММ.")

                # Парсинг дней недели. _parse_days выбрасывает ValueError при неверном названии дня
                days = self._parse_days(days_str)

                # Если парсинг успешен, устанавливаем атрибуты
                self.trigger = CronTrigger(hour=hour, minute=minute, day_of_week=days)
                self.str_trgger_time = f'{time_str} {days_str}' # Сохраняем строку, как ввел пользователь

            except ValueError as e:
                 # Логируем ошибку и перебрасываем исключение с более понятным сообщением
                 logger.error(f"Ошибка создания Cron триггера из '{trigger_time}': {e}")
                 # Перебрасываем исключение, сохраняя исходное сообщение ошибки парсинга
                 raise ValueError(f"Ошибка парсинга Cron триггера: {e}")


        elif trigger_type == 1:  # IntervalTrigger (число единица)
            try:
                # Пробуем разделить строку на число и единицу
                interval_str = trigger_time.strip()
                parts = interval_str.split()

                if len(parts) != 2:
                    raise ValueError("Неверный формат. Ожидается: '15 часов' или '11 минут'.")

                # Парсинг числа интервала
                try:
                    interval = int(parts[0])
                except ValueError:
                     raise ValueError(f"Интервал должен быть числом. Получено: '{parts[0]}'.")

                if interval <= 0:
                    raise ValueError("Интервал должен быть положительным числом.")

                # Парсинг единицы измерения
                unit = parts[1].lower()
                unit_mapping = {
                    "мин": "minutes", "час": "hours", "ден": "days", "дн": "days",
                    "минута": "minutes", "минуты": "minutes", "минут": "minutes",
                    "час": "hours", "часа": "hours", "часов": "hours",
                    "день": "days", "дня": "days", "дней": "days",
                }
                unit_type = None
                # Пробуем найти точное совпадение или по началу слова
                if unit in unit_mapping:
                    unit_type = unit_mapping[unit]
                else:
                     # Попробуем по первым символам, если точного совпадения нет
                     for key, val in unit_mapping.items():
                         if unit.startswith(key):
                             unit_type = val
                             break


                if unit_type is None:
                    raise ValueError(f"Неверная единица измерения: '{unit}'. Допустимые значения: 'минуты', 'часы', 'дни'.")

                # Если парсинг успешен, устанавливаем атрибуты
                self.trigger = IntervalTrigger(**{unit_type: interval})
                self.str_trgger_time = interval_str # Сохраняем строку, как ввел пользователь

            except ValueError as e:
                 # Логируем ошибку и перебрасываем исключение с более понятным сообщением
                 logger.error(f"Ошибка создания Interval триггера из '{trigger_time}': {e}")
                 raise ValueError(f"Ошибка парсинга Interval триггера: {e}")


        elif trigger_type == 3: # DateTrigger (точная дата и время ЧЧ:ММ ДД.ММ.ГГ или ЧЧ:ММ ДД.ММ.ГГГГ)
            try:
                # Пробуем разделить строку на время и дату. Ожидаем 2 части
                parts = trigger_time.strip().split(' ')
                if len(parts) != 2:
                    trigger_time = '00:00 ' + trigger_time
                    parts = trigger_time.strip().split(' ')

                time_part, date_part = parts # Ожидаем формат "ЧЧ:ММ ДД.ММ.ГГ[ГГ]"

                dt = None
                last_exception = None

                # 1. Пробуем формат с полным годом: ЧЧ:ММ ДД.ММ.ГГГГ
                try:
                     dt = datetime.strptime(f"{date_part} {time_part}", "%d.%m.%Y %H:%M")
                except ValueError as e:
                     last_exception = e # Сохраняем ошибку, если не удалось

                # 2. Если полный год не подошел, пробуем формат с коротким годом: ЧЧ:ММ ДД.ММ.ГГ
                if dt is None:
                    try:
                         dt = datetime.strptime(f"{date_part} {time_part}", "%d.%m.%y %H:%M")
                    except ValueError as e:
                         last_exception = e # Сохраняем последнюю ошибку

                # Если после обеих попыток дата не распарсилась, выбрасываем ошибку
                if dt is None:
                     # Выбрасываем ошибку парсинга. Можно включить сообщение последней ошибки strptime
                     raise ValueError(f"Неверный формат даты или времени. Ожидается ЧЧ:ММ ДД.ММ.ГГ или ЧЧ:ММ ДД.ММ.ГГГГ.")
                         # Если нужно показать ошибку strptime: raise ValueError(f"Ошибка парсинга даты или времени: {last_exception}. Ожидается ЧЧ:ММ ДД.ММ.ГГ или ЧЧ:ММ ДД.ММ.ГГГГ.")


                # Проверка, что дата в будущем (сравниваем без секунд/микросекунд)
                now = datetime.now().replace(second=0, microsecond=0)
                if dt < now:
                    raise ValueError("Дата и время напоминания должны быть в будущем.")

                # Если парсинг и проверка на будущее успешны, устанавливаем атрибуты
                self.trigger = DateTrigger(run_date=dt)
                self.str_trgger_time = dt.strftime("%d.%m.%y %H:%M") # Сохраняем объект datetime

            except ValueError as e:
                 # Логируем ошибку и перебрасываем исключение с более понятным сообщением
                 logger.error(f"Ошибка создания Date триггера из '{trigger_time}': {e}")
                 raise ValueError(f"Ошибка парсинга даты/времени: {e}") # Перебрасываем исключение, сохраняя исходное сообщение об ошибке (например, "Дата в прошлом")
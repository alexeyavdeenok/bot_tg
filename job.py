from datetime import datetime
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from logger import logger

day_convert = {
    "понедельник": 0,
    "вторник": 1,
    "среда": 2,
    "четверг": 3,
    "пятница": 4,
    "суббота": 5,
    "воскресенье": 6}

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

    async def delete_job(self, index):
        await self.db.delete_reminder(self.job_list[index].job_id)
        self.job_list.pop(index)
        

    def import_job_from_schedule(self, event, date_str):
        event_time = event.start
        event_date = date_str.strftime("%d.%m.%Y")
        event_for_job = event_time + " " + event_date
        job = Job(event.title, 3, event_for_job)

    def import_job_from_todolist(self, task):
        job = Job(task.title, 3, task.deadline.strftime("%d.%m.%Y"))
        

class Job:
    def __init__(self, job_name, trigger_type, trigger_time):
        self.job_name = job_name
        self.set_trigger(trigger_type, trigger_time)
        self.job_id = None
        self.text_job = None
        self.str_trgger_time = None

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
        if trigger_type == 2:  # CronTrigger
            parts = trigger_time.strip().rsplit(' ', 1)

            days_str, time_str = parts

            try:
                datetime.strptime(time_str, "%H:%M")
            except ValueError:
                raise ValueError(f"Неверный формат времени: '{time_str}'")

            hour, minute = map(int, time_str.split(':'))
            
            days = self._parse_days(days_str)

            self.str_trgger_time = f'{days_str} {time_str}'

            self.trigger = CronTrigger(
                hour=hour,
                minute=minute,
                day_of_week=days
            )
        elif trigger_type == 1:  # IntervalTrigger
            # Попытка разделить строку на количество и единицу измерения
            try:
                interval_str = trigger_time.strip()
                parts = interval_str.split()
                
                if len(parts) != 2:
                    raise ValueError("Неверный формат интервала. Ожидается: '15 часов' или '11 минут'")
                
                interval = int(parts[0])
                unit = parts[1].lower()
                
                # Определение единицы измерения по первым трем буквам
                if unit.startswith("ден") or unit.startswith("дн"):
                    unit_type = "days"
                elif unit.startswith("час"):
                    unit_type = "hours"
                elif unit.startswith("мин"):
                    unit_type = "minutes"
                else:
                    raise ValueError(f"Неверная единица измерения: '{unit}'. Допустимые значения: 'дни', 'часы', 'минуты'")
                
                if interval <= 0:
                    raise ValueError("Интервал должен быть положительным числом")
                
                self.str_trgger_time = f"{interval} {unit}"
                
                self.trigger = IntervalTrigger(**{unit_type: interval})
            except ValueError as e:
                raise ValueError(f"Ошибка парсинга интервала: {str(e)}")
        else:
            try:
                time_str, date_str = trigger_time.strip().split(' ')
                
                dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%y %H:%M")
                
                now = datetime.now()
                if dt < now:
                    raise ValueError("Дата должна быть в будущем")
                
                self.str_trgger_time = dt
                
                self.trigger = DateTrigger(run_date=dt)
            except ValueError as e:
                raise ValueError(f"Ошибка парсинга даты/времени: {str(e)}. Формат: ДД.ММ.ГГ ЧЧ:ММ")
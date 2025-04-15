from datetime import datetime
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

day_convert = {
    "понедельник": 0,
    "вторник": 1,
    "среда": 2,
    "четверг": 3,
    "пятница": 4,
    "суббота": 5,
    "воскресенье": 6}

class JobList:
    def __init__(self):
        self.job_list = []

    def import_job_from_schedule(self):
        pass

    def import_job_from_todolist(self):
        pass


class Job:
    def __init__(self, job_name, trigger):
        self.job_name = None
        self.trigger = trigger
        job_id = None
        text_job = None

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

            self.trigger = CronTrigger(
                hour=hour,
                minute=minute,
                day_of_week=days
            )
        elif trigger_type == 1:  # IntervalTrigger
            pass
        else:
            try:
                date_str, time_str = trigger_time.strip().split(' ')
                
                dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%y %H:%M")
                
                now = datetime.now()
                if dt < now:
                    raise ValueError("Дата должна быть в будущем")
                
                self.trigger = DateTrigger(run_date=dt)
            except ValueError as e:
                raise ValueError(f"Ошибка парсинга даты/времени: {str(e)}. Формат: ДД.ММ.ГГ ЧЧ:ММ")
            

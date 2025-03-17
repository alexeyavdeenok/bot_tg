from datetime import date, timedelta, datetime
import asyncio
days_of_week = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']


class Schedule:
    def __init__(self, user_id, db):
        self.user_id = user_id
        self.db = db
        self.weeks = self.set_weeks()
        self.current_day = self.get_current_day()
        self.week_to_show = self.current_week
        self.day_to_show = self.current_day
        #asyncio.create_task(self.load_events())  # Загрузка событий в фоновом режиме

    async def load_events(self):
        """Загружает события из базы и распределяет их по дням."""
        events = await self.db.get_schedule_events(self.user_id)
        for event in events:
            date_str = event[1]
            day = self.find_day_by_date(date_str)
            if day:
                day.add_event(event[2], event[3], event[4], event[5], event[0])

    def find_day_by_date(self, date_str):
        """Находит день в неделях по дате."""
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        for week in self.weeks:
            for day in week.list_days:
                if day.date_ == target_date:
                    return day
        return None
    
    def save_to_database(self):
        """Сохраняет текущее расписание в базу данных."""
        for week in self.weeks:
            for day in week.list_days:
                for event in day.list_events:
                    asyncio.create_task(
                        self.db.add_schedule_event(
                            self.user_id,
                            day.date_.strftime("%Y-%m-%d"),
                            event.start,
                            event.end,
                            event.title,
                            event.is_important
                        )
                    )

    def set_weeks(self):
        current_day = date.today()
        first_day = current_day - timedelta(days=current_day.weekday())  # Понедельник текущей недели
        list_weeks = []
        for i in range(-2, 3):  # От -2 до +2 недель
            week_start = first_day + timedelta(days=7 * i)
            list_weeks.append(Week(week_start))
        self.current_week = list_weeks[2]  # Текущая неделя — третья
        return list_weeks

    def get_current_day(self):
        for i in self.current_week.list_days:
            if date.today() == i.date_:
                i.is_current = True
                return i

    def get_current_week(self):
        current_day = date.today()
        first_day = current_day - timedelta(days=current_day.weekday())
        for i in self.weeks:
            if i.first_day == first_day:
                return i
            
    def next_day(self):
        if self.day_to_show.index == 6:
            self.next_week()
            self.day_to_show = self.week_to_show.list_days[0]
        else:
            self.day_to_show = self.week_to_show.list_days[self.day_to_show.index + 1]

    def prev_day(self):
        if self.day_to_show.index == 0:
            self.prev_week()
            self.day_to_show = self.week_to_show.list_days[6]
        else:
            self.day_to_show = self.week_to_show.list_days[self.day_to_show.index - 1]

    def next_week(self):
        if self.week_to_show == self.weeks[-1]:
            pass
        else:
            self.week_to_show = self.weeks[self.weeks.index(self.week_to_show) + 1]

    def prev_week(self):
        if self.week_to_show == self.weeks[0]:
            pass
        else:
            self.week_to_show = self.weeks[self.weeks.index(self.week_to_show) - 1]

    def delete_event(self, index):
        self.day_to_show.delete_event(index)
    
    def add_event(self, start_time, end_time, title, is_important=True, event_id=None):
        self.day_to_show.add_event(start_time, end_time, title, is_important, event_id)

    def change_important(self, index):
        self.day_to_show.list_events[index].change_important()

    def choose_day(self, index):
        self.day_to_show = self.week_to_show.list_days[index]
    
    def return_to_current_day(self):
        self.day_to_show = self.current_day
    
    def return_to_current_week(self):
        self.week_to_show = self.current_week
    
    @staticmethod
    def sort_by_time(event_elem):
        start_hours, start_minutes = map(int, event_elem.start.split(':'))
        return start_hours * 60 + start_minutes

    @staticmethod
    def validate_event_time(start_time, end_time):
        """Проверяет, что время начала раньше времени конца."""
        start_hours, start_minutes = map(int, start_time.split(':'))
        end_hours, end_minutes = map(int, end_time.split(':'))
        
        start_total = start_hours * 60 + start_minutes
        end_total = end_hours * 60 + end_minutes
        
        if start_total >= end_total:
            raise ValueError("Время начала должно быть раньше времени окончания.")
        
        return True
    
    def update(self):
        # Получаем текущую дату
        today = date.today()
        # Вычисляем дату начала текущей недели (понедельник)
        current_first_day = today - timedelta(days=today.weekday())

        # Проверяем, изменилась ли текущая неделя
        if current_first_day == self.current_week.first_day:
            # Неделя не изменилась, обновляем только текущий день
            self.current_day.is_current = False  # Снимаем метку с предыдущего дня
            self.current_day = self.current_week.list_days[today.weekday()]
            self.current_day.is_current = True
        else:
            # Неделя изменилась, пересоздаем список недель
            # Формируем даты начала для 5 недель: -2, -1, 0, +1, +2 относительно текущей
            first_days = [current_first_day + timedelta(days=7 * i) for i in range(-2, 3)]
            new_weeks = [Week(fd) for fd in first_days]

            # Сохраняем события из старых дней
            old_days = {day.date_: day.list_events for week in self.weeks for day in week.list_days}

            # Копируем события в новые дни, если даты совпадают
            for week in new_weeks:
                for day in week.list_days:
                    if day.date_ in old_days:
                        day.list_events = old_days[day.date_]

            # Обновляем атрибуты
            self.weeks = new_weeks
            self.current_week = self.weeks[2]  # Текущая неделя — третья в списке
            self.current_day = self.current_week.list_days[today.weekday()]
            self.current_day.is_current = True

        # Обновляем отображаемые значения
        self.week_to_show = self.current_week
        self.day_to_show = self.current_day


class Week:
    def __init__(self, first_day):
        self.first_day = first_day
        self.list_days = self.create_week(first_day)

    def create_week(self, first_day):
        week = []
        day = first_day
        for i in range(7):
            week.append(Day(day))
            day += timedelta(days=1)
        return week
    
    def __str__(self):
        return '\n'.join(i.str_for_weeks() for i in self.list_days)
        

class Day:
    def __init__(self, date_str, list_events=None, is_current=False):
        self.is_current = is_current
        self.date_ = date_str
        self.list_events = list_events if list_events is not None else []
        self.index = self.date_.weekday()
        self.weekday_name = days_of_week[self.index]

    def change_current(self):
        self.is_current = not self.is_current

    def add_event(self, start_time, end_time, title, is_important=True, event_id=None):
        self.list_events.append(Event(start_time, end_time, title, is_important, event_id))
        self.list_events.sort(key=Schedule.sort_by_time)
    
    def delete_event(self, index):
        self.list_events.pop(index)
        self.list_events.sort(key=Schedule.sort_by_time)

    def str_for_weeks(self):
        return f'<b>{days_of_week[self.date_.weekday()]} {self.date_.strftime("%d.%m.%Y")}</b>\n'+'\n'.join(str(i) for i in self.list_events if i.is_important) + f'\n{'=' * 30}'
    
    
    def __str__(self):
        return f'{days_of_week[self.date_.weekday()]} {self.date_.strftime("%d.%m.%Y")}\n' f'{'_'*35}\n'+'\n'.join(str(i) for i in self.list_events) + f'\n{'=' * 30}'


class Event:
    def __init__(self, start, end, title, is_important=True, event_id=None):
        self.set_start(start)
        self.set_end(end)
        self.title = title
        self.is_important = is_important
        self.event_id = event_id
    
    def __str__(self):
        return f"{self.start} - {self.end} | {self.title}"
    
    def set_start(self, start):
        first, second = start.split(':')
        if int(first) >= 0 and int(first) < 10:
            #first = '0' + first
            pass
        elif int(first) >= 10 and int(first) <= 24:
            pass
        else:
            raise ValueError('Неверное время')
        if int(second) >= 0 and int(second) < 60 and len(second) == 2:
            pass
        else:
            raise ValueError('Неверное время')
        self.start = f"{first}:{second}"
    
    def set_end(self, end):
        first, second = end.split(':')
        if int(first) >= 0 and int(first) < 10:
            #first = '0' + first
            pass
        elif int(first) >= 10 and int(first) <= 24:
            pass
        else:
            raise ValueError('Неверное время')
        if int(second) >= 0 and int(second) < 60 and len(second) == 2:
            pass
        else:
            raise ValueError('Неверное время')
        self.end = f"{first}:{second}"
    
    def change_important(self):
        if self.is_important:
            self.is_important = False
        else:
            self.is_important = True
        

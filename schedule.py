from datetime import date, timedelta

days_of_week = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']


class Schedule:
    def __init__(self):
        self.weeks = self.set_weeks()
        self.current_day = self.get_current_day()
        self.week_to_show = self.current_week
        self.day_to_show = self.current_day
    
    def set_weeks(self):
        current_day = date.today()
        first_day = current_day - timedelta(days=current_day.weekday())
        week = Week(first_day)
        list_weeks = [week]
        self.current_week = week
        for i in range(2):
            first_day += timedelta(days=7)
            week = Week(first_day)
            list_weeks.append(week)
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
        return '\n'.join(str(i) for i in self.list_days)
        
class Day:
    def __init__(self, date_str, list_events=None, is_current=False):
        self.is_current = is_current
        self.date_ = date_str
        self.list_events = list_events if list_events is not None else []

    def change_current(self):
        self.current = not self.current

    def add_event(self, start_time, end_time, title, is_important=False):
        self.list_events.append(Event(start_time, end_time, title, is_important))
    
    def delete_event(self, index):
        self.list_events.pop(index)
    
    def __str__(self):
        return f'{days_of_week[self.date_.weekday()]} {self.date_.strftime("%d.%m.%Y")}\n' + '\n'.join(str(i) for i in self.list_events)

class Event:
    def __init__(self, start, end, title, is_important=False):
        self.set_start(start)
        self.set_end(end)
        self.title = title
        self.is_important = is_important
    
    def __str__(self):
        return f"{self.start} - {self.end} | {self.title}"
    
    def set_start(self, start):
        first, second = start.split(':')
        if int(first) >= 0 and int(first) < 10:
            first = '0' + first
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
            first = '0' + first
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


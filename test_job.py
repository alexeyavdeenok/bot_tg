import unittest
from datetime import datetime, timedelta
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from job import Job

class TestJobCreation(unittest.TestCase):
    def test_cron_trigger_creation(self):
        """Тест создания CronTrigger с корректными днями и временем."""
        job = Job("Утреннее напоминание", 2, "понедельник, среда, пятница 08:30")
        self.assertIsInstance(job.trigger, CronTrigger)

        # Проверяем корректность дней недели
        days_field = job.trigger.fields[4]  # Поле дней недели
        self.assertEqual(str(days_field), "0,2,4")  # понедельник = 0, среда = 2, пятница = 4

        # Проверяем часы и минуты
        self.assertEqual(str(job.trigger.fields[5]), "8")

        self.assertEqual(job.trigger.fields[6].__str__(), "30")  # Минуты

    def test_interval_trigger_creation_minutes(self):
        """Тест создания IntervalTrigger с интервалом в минуты."""
        job = Job("Короткий перерыв", 1, "15 минут")
        self.assertIsInstance(job.trigger, IntervalTrigger)
        self.assertEqual(job.trigger.interval.total_seconds(), 15 * 60)  # Проверяем секунды

    def test_interval_trigger_creation_hours(self):
        """Тест создания IntervalTrigger с интервалом в часы."""
        job = Job("Часовое напоминание", 1, "2 часа")
        self.assertIsInstance(job.trigger, IntervalTrigger)
        self.assertEqual(job.trigger.interval.total_seconds(), 2 * 60 * 60)  # Проверяем секунды

    def test_interval_trigger_creation_days(self):
        """Тест создания IntervalTrigger с интервалом в дни."""
        job = Job("Ежедневное напоминание", 1, "1 день")
        self.assertIsInstance(job.trigger, IntervalTrigger)
        self.assertEqual(job.trigger.interval.total_seconds(), 24 * 60 * 60)  # Проверяем секунды

    def test_date_trigger_creation_full_year(self):
        """Тест создания DateTrigger с полным годом."""
        future_date = (datetime.now() + timedelta(days=1)).strftime("%H:%M %d.%m.%Y")
        job = Job("Будущее событие", 3, future_date)
        self.assertIsInstance(job.trigger, DateTrigger)
        self.assertEqual(job.trigger.run_date.strftime("%H:%M %d.%m.%Y"), future_date)

    def test_date_trigger_creation_short_year(self):
        """Тест создания DateTrigger с коротким годом."""
        future_date = (datetime.now() + timedelta(days=1)).strftime("%H:%M %d.%m.%y")
        job = Job("Короткий формат года", 3, future_date)
        self.assertIsInstance(job.trigger, DateTrigger)
        self.assertEqual(job.trigger.run_date.strftime("%H:%M %d.%m.%y"), future_date)

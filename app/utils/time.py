from datetime import datetime, timedelta

import config

from app.models.enums import DayType


class ScheduleTime:
    time_week = 604800
    start_semester = config.START_SEMESTER
    base_week_delta = config.BASE_WEEK_DELTA

    @classmethod
    def week_delta(cls, delta: int):
        return delta + cls.base_week_delta

    @classmethod
    def compute_current_week(cls) -> int:
        return int((cls.compute_timestamp() - cls.start_semester) / cls.time_week) + 1

    @classmethod
    def compute_timestamp_for_api(cls, week_delta: int = 0) -> str:
        return f"{cls.compute_timestamp(week_delta=week_delta)}000"

    @classmethod
    def compute_timestamp(cls, week_delta: int = 0) -> int:
        time = datetime.utcnow()
        time = datetime(year=time.year, month=time.month, day=time.day, minute=5)
        time = int((time - timedelta(days=time.weekday())).timestamp())

        return time + (cls.week_delta(week_delta)) * cls.time_week

    @classmethod
    def compute_datetime(cls, week_delta: int = 0):
        return datetime.fromtimestamp(cls.compute_timestamp(week_delta))

    @classmethod
    def today(cls) -> DayType:
        day = datetime.utcnow().weekday()
        if day == 6:
            return DayType.Monday
        return DayType(day)

    @classmethod
    def next_day(cls) -> DayType:
        day = datetime.utcnow().weekday()
        if day == 5 or day == 6:
            return DayType.Monday

        return DayType(day + 1)

    @classmethod
    def previous_day(cls) -> DayType:
        day = datetime.utcnow().weekday()
        if day == 0 or day == 6:
            return DayType.Saturday

        return DayType(day - 1)
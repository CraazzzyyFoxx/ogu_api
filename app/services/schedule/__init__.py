from __future__ import annotations

from datetime import datetime

import pytz
from loguru import logger
from tortoise.expressions import Q
from tortoise.query_utils import Prefetch

import config
from .api import HTTPClient

from app.utils.time import ScheduleTime
from app.models.enums import ActionStats, Years, DayType, UserType
from app.models.db import (ScheduleModel,
                           ScheduleSubjectModel,
                           StatsModel,
                           FacultyModel,
                           DepartmentModel,
                           EmployeeModel,
                           GroupModel,
                           ExamModel
                           )


class ScheduleService:
    http: HTTPClient = None

    @classmethod
    async def init(cls):
        cls.http = HTTPClient()
        await cls.http.initialize()
        last_update = await StatsModel.filter(action=ActionStats.fetch_data).order_by("-datetime").first()
        if not last_update or await cls._check_update(ActionStats.fetch_data):
            await cls._update_data()

    @classmethod
    def timestamp_q(cls, week_delta: int):
        if week_delta < 0:
            return (Q(date__gte=ScheduleTime.compute_timestamp(week_delta=week_delta + 1))
                    & Q(date__lte=ScheduleTime.compute_timestamp(week_delta=week_delta)))
        else:
            return (Q(date__gte=ScheduleTime.compute_timestamp(week_delta=week_delta))
                    & Q(date__lte=ScheduleTime.compute_timestamp(week_delta=week_delta + 1)))

    @classmethod
    async def _update_data(cls):
        faculties = await cls.fetch_faculties()
        for faculty in faculties:
            departments = await cls.fetch_departments(faculty.id)
            for department in departments:
                await cls.fetch_employees(department.id)
            await cls.fetch_groups(faculty.id)

        await StatsModel.create(action=ActionStats.fetch_data, datetime=datetime.utcnow())

    @classmethod
    async def _check_update(cls, action: ActionStats, user = None) -> bool:
        tdict = {
            ActionStats.fetch_schedule: config.UPDATE_FETCH_SCHEDULE,
            ActionStats.fetch_exams: config.UPDATE_FETCH_EXAMS,
            ActionStats.fetch_faculties: config.UPDATE_FETCH_FACULTIES,
            ActionStats.fetch_departments: config.UPDATE_FETCH_DEPARTMENTS,
            ActionStats.fetch_employees: config.UPDATE_FETCH_EMPLOYEES,
            ActionStats.fetch_employee: config.UPDATE_FETCH_EMPLOYEE,
            ActionStats.fetch_data: config.UPDATE_FETCH_DATA
        }

        if user:
            last_update = await StatsModel.filter(action=action, object_id=user.id).order_by("-datetime").first()
        else:
            last_update = await StatsModel.filter(action=action).order_by("-datetime").first()
        if not last_update:
            return True

        if last_update.datetime < (datetime.utcnow() - tdict[action]).astimezone(pytz.utc):
            return True

        return False

    @classmethod
    async def fetch_faculties(
            cls,
            with_save: bool = True
    ) -> list[FacultyModel]:
        faculties = await cls.http.get_faculties()

        faculty_models = [FacultyModel(id=faculty.id,
                                       title=faculty.title,
                                       short_title=faculty.short_title) for faculty in faculties]

        if with_save:
            await FacultyModel.all().delete()
            await FacultyModel.bulk_create(faculty_models, ignore_conflicts=True)
            await StatsModel.create(action=ActionStats.fetch_faculties, datetime=datetime.utcnow())

        logger.info("Fetched faculties")

        return faculty_models

    @classmethod
    async def fetch_departments(
            cls,
            faculty_id: int,
            with_save: bool = True
    ) -> list[DepartmentModel]:
        departments = await cls.http.get_departments(faculty_id)
        department_models = [DepartmentModel(id=department.id,
                                             title=department.title,
                                             short_title=department.short_title,
                                             faculty_id=faculty_id) for department in departments]

        if with_save:
            await DepartmentModel.filter(Q(faculty_id=faculty_id)).delete()
            await DepartmentModel.bulk_create(department_models, ignore_conflicts=True)
            await StatsModel.create(action=ActionStats.fetch_departments, datetime=datetime.utcnow())

        logger.info("Fetched departments for {} faculty", faculty_id)

        return department_models

    @classmethod
    async def fetch_employees(
            cls,
            department_id: int,
            with_save: bool = True
    ) -> list[EmployeeModel]:
        employees = await cls.http.get_employees(department_id)
        employee_models = [EmployeeModel(id=employee.id,
                                         name=employee.name,
                                         second_name=employee.second_name,
                                         middle_name=employee.middle_name,
                                         department_id=department_id) for employee in employees]

        if with_save:
            await EmployeeModel.filter(Q(department_id=department_id)).delete()
            await EmployeeModel.bulk_create(employee_models, ignore_conflicts=True)
            await StatsModel.create(action=ActionStats.fetch_employees, datetime=datetime.utcnow())

        logger.info("Fetched employees for {} department", department_id)

        return employee_models

    @classmethod
    async def fetch_groups(
            cls,
            faculty_id: int,
            with_save: bool = True
    ) -> dict[Years, list[GroupModel]]:
        group_map: dict[Years, list[GroupModel]] = {}
        for course in Years:
            groups = await cls.http.get_groups(faculty_id, course)
            if not groups:
                continue
            group_models = [GroupModel(id=group.id,
                                       course=course,
                                       direction=group.direction,
                                       level=group.level.value,
                                       name=group.name,
                                       faculty_id=faculty_id) for group in groups]
            group_map[course] = group_models

            if with_save:
                await GroupModel.filter(Q(faculty_id=faculty_id) & Q(course=course)).delete()
                await GroupModel.bulk_create(group_models, ignore_conflicts=True)
                await StatsModel.create(action=ActionStats.fetch_groups, datetime=datetime.utcnow())

        logger.info("Fetched groups for {} faculty", faculty_id)

        return group_map

    @classmethod
    async def fetch_schedule(
            cls,
            user,
            week_delta: int = 0,
            with_save: bool = True
    ) -> dict[DayType, ScheduleModel]:
        if user.type == UserType.Student:
            schedule = await cls.http.get_schedule_student(user.group_id, week_delta=week_delta)
        else:
            schedule = await cls.http.get_schedule_employee(user.employee_id, week_delta=week_delta)
        if not schedule:
            return {}

        subject_map: dict[DayType, ScheduleModel] = {}

        for schedule_day in schedule.days.values():
            schedule_m = await ScheduleModel.filter(cls.timestamp_q(week_delta) & Q(day=schedule_day.day)).first()

            if not schedule_m:
                schedule_m = ScheduleModel(day=schedule_day.day, date=schedule_day.date)

            subjects = [ScheduleSubjectModel(**subject.dict(exclude={"employee_name",
                                                                     "employee_second_name",
                                                                     "employee_middle_name"}))
                        for subject in schedule_day.subjects]

            if with_save:
                if not schedule_m._saved_in_db:
                    await schedule_m.save()

                subjects = []

                for subject in schedule_day.subjects:
                    s_m = ScheduleSubjectModel(schedule_id=schedule_m.id,
                                               **subject.dict(exclude={"employee_name",
                                                                       "employee_second_name",
                                                                       "employee_middle_name"}))
                    s_m.employee = EmployeeModel(id=subject.employee_id,
                                                 name=subject.employee_name,
                                                 second_name=subject.employee_second_name,
                                                 middle_name=subject.employee_middle_name)
                    s_m.employee._fetched = True

                    s_m.group = GroupModel(id=subject.group_id,
                                           name=subject.title)
                    s_m.group._fetched = True

                    subjects.append(s_m)

                await ScheduleSubjectModel.bulk_create(subjects, on_conflict=("schedule_id", "employee_id", "number"),
                                                       update_fields=("name",
                                                                      "sub_group",
                                                                      "audience",
                                                                      "building",
                                                                      "type",
                                                                      "zoom_link",
                                                                      "zoom_password"))

            schedule_m.subjects.related_objects = subjects
            schedule_m.subjects._fetched = True

            subject_map[schedule_day.day] = schedule_m

        if with_save:
            await StatsModel.create(action=ActionStats.fetch_schedule, object_id=user.id, datetime=datetime.utcnow())

        logger.info("Fetched schedule for {} user", user.id)

        return subject_map

    @classmethod
    async def fetch_exams(cls, user, with_save: bool = True) -> list[ExamModel]:
        if user.type == UserType.Student:
            schedule = await cls.http.get_exams_student(user.group_id)
            user_q = Q(group_id=user.group_id)
        else:
            schedule = await cls.http.get_exams_employee(user.employee_id)
            user_q = Q(employee_id=user.employee_id)
        if not schedule:
            return []

        subjects = [ExamModel(**exam.dict(exclude={"employee_name",
                                                   "employee_second_name",
                                                   "employee_middle_name"}))
                    for exam in schedule]

        if with_save:
            await ExamModel.filter(user_q).delete()
            await ExamModel.bulk_create(subjects, ignore_conflicts=True)
            await StatsModel.create(action=ActionStats.fetch_exams, object_id=user.id, datetime=datetime.utcnow())

        logger.info("Fetched exams {} for user", user.id)

        return subjects

    @classmethod
    async def get_faculties(cls) -> list[FacultyModel]:
        return await FacultyModel.all()

    @classmethod
    async def get_departments(cls, faculty_id: int) -> list[DepartmentModel]:
        return await DepartmentModel.filter(faculty_id=faculty_id)

    @classmethod
    async def get_employees(cls, department_id: int) -> list[EmployeeModel]:
        return await EmployeeModel.filter(department_id=department_id)

    @classmethod
    async def get_schedule(
            cls,
            user,
            week_delta: int = 0,
            with_update: bool = True
    ) -> dict[DayType, ScheduleModel]:
        # if with_update and await cls._check_update(action=ActionStats.fetch_schedule, user=user):
        #     return await cls.fetch_schedule(user, week_delta=week_delta)
        # await fetch_schedule_ratelimiter.acquire(user)
        # if with_update and not fetch_schedule_ratelimiter.is_rate_limited(user):
        #     return await cls.fetch_schedule(user, week_delta=week_delta)

        user_q = Q(group_id=user.group_id) if user.type == UserType.Student else Q(employee_id=user.employee_id)
        models = (await ScheduleModel
                  .filter(cls.timestamp_q(week_delta))
                  .prefetch_related(Prefetch("subjects", queryset=ScheduleSubjectModel.filter(user_q)
                                             .prefetch_related("group", "employee"))))

        subject_map: dict[DayType, ScheduleModel] = {day: None for day in DayType}
        ...
        for model in models:
            subject_map[model.day] = model

        return subject_map

    @classmethod
    async def get_exams(
            cls,
            user,
            with_update: bool = True,
    ) -> list[ExamModel]:
        # if with_update and await cls._check_update(action=ActionStats.fetch_exams, user=user):
        #     return await cls.fetch_exams(user)

        # if with_update and not fetch_exams_ratelimiter.is_rate_limited(user):
        #     return await cls.fetch_exams(user)

        user_q = Q(group_id=user.group_id) if user.type == UserType.Student else Q(employee_id=user.employee_id)
        return await ExamModel.filter(user_q).prefetch_related("employee", "group")

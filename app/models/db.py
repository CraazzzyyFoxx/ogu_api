from __future__ import annotations

import typing

from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.models import Model

from app.models.enums import DayType, EducationalLevel, Years, SubjectType, ActionStats

__all__: typing.Sequence[str] = (
    "ScheduleModel",
    "ScheduleSubjectModel",
    "EmployeeModel",
    "FacultyModel",
    "GroupModel",
    "StatsModel",
    "CookieModel",
    "UserAgentModel",
    "DepartmentModel",
    "ExamModel",
    "Faculty",
    "Department",
    'Employee',
    'ScheduleSubject',
    'Exam'

)


class TokenModel(Model):
    token = fields.TextField()
    scopes = fields.JSONField(default="{}")
    ratelimits = fields.JSONField(default="{}")

    class Meta:
        """Metaclass to set table name and description"""

        table = "token"
        table_description = "Stores information about the token"


class StatsModel(Model):
    id = fields.IntField(pk=True)
    action = fields.IntEnumField(ActionStats)
    datetime = fields.DatetimeField(auto_now_add=True)
    object_id = fields.BigIntField(null=True)
    extra = fields.JSONField(default="{}")

    class Meta:
        """Metaclass to set table name and description"""

        table = "stats"
        table_description = "Stores information about the stats"


class CookieModel(Model):
    id = fields.BigIntField(pk=True)
    datetime = fields.DatetimeField(auto_now_add=True)
    extra = fields.TextField()

    class Meta:
        """Metaclass to set table name and description"""

        table = "cookie"
        table_description = "Stores information about the cookies"


class UserAgentModel(Model):
    id = fields.BigIntField(pk=True)
    datetime = fields.DatetimeField(auto_now_add=True)
    extra = fields.TextField()

    class Meta:
        """Metaclass to set table name and description"""

        table = "user_agent"
        table_description = "Stores information about the user_agent"


class FacultyModel(Model):
    id = fields.IntField(pk=True, generated=False)
    title = fields.TextField()
    short_title = fields.TextField()

    groups: fields.ReverseRelation["GroupModel"]
    departments: fields.ReverseRelation["DepartmentModel"]

    class Meta:
        """Metaclass to set table name and description"""

        table = "faculty"
        table_description = "Stores information about the faculty"


class DepartmentModel(Model):
    id = fields.IntField(pk=True, generated=False)
    title = fields.TextField()
    short_title = fields.TextField()

    employees: fields.ReverseRelation["EmployeeModel"]
    faculty: fields.ForeignKeyRelation["FacultyModel"] = fields.ForeignKeyField(model_name='main.FacultyModel',
                                                                                related_name='departments',
                                                                                to_field='id')

    class Meta:
        """Metaclass to set table name and description"""

        table = "department"
        table_description = "Stores information about the department"


class GroupModel(Model):
    id = fields.IntField(pk=True, generated=False)
    direction = fields.TextField()
    course = fields.IntEnumField(Years)
    level = fields.IntEnumField(EducationalLevel)
    name = fields.TextField()

    faculty: fields.ForeignKeyRelation["FacultyModel"] = fields.ForeignKeyField(model_name='main.FacultyModel',
                                                                                related_name='groups',
                                                                                to_field='id')

    class Meta:
        """Metaclass to set table name and description"""

        table = "group"
        table_description = "Stores information about the group"


class EmployeeModel(Model):
    id = fields.IntField(pk=True, generated=False)
    name = fields.TextField()
    second_name = fields.TextField()
    middle_name = fields.TextField()

    schedule: fields.ReverseRelation['ScheduleModel']
    exams: fields.ReverseRelation['ExamModel']
    department: fields.ForeignKeyRelation["DepartmentModel"] = fields.ForeignKeyField(model_name='main.DepartmentModel',
                                                                                      related_name='employees',
                                                                                      to_field='id')

    class Meta:
        """Metaclass to set table name and description"""

        table = "employee"
        table_description = "Stores information about the employee"


class ScheduleModel(Model):
    id = fields.IntField(pk=True)
    day = fields.IntEnumField(DayType)
    date = fields.IntField()

    subjects: fields.ForeignKeyRelation[ScheduleSubjectModel]

    class Meta:
        """Metaclass to set table name and description"""

        table = "schedule"
        table_description = "Stores information about the schedule"
        unique_together = ("day", "date")


class ScheduleSubjectModel(Model):
    id = fields.IntField(pk=True)

    name = fields.TextField()
    sub_group = fields.IntField()
    audience = fields.TextField()
    building = fields.SmallIntField()
    number = fields.SmallIntField()
    type = fields.IntEnumField(SubjectType)

    zoom_link = fields.TextField(null=True)
    zoom_password = fields.TextField(null=True)

    schedule: fields.ForeignKeyRelation[ScheduleModel] = fields.ForeignKeyField(model_name="main.ScheduleModel",
                                                                                related_name='subjects',
                                                                                to_field='id')

    employee: fields.ForeignKeyRelation[EmployeeModel] = fields.ForeignKeyField(model_name='main.EmployeeModel',
                                                                                related_name='subjects',
                                                                                to_field='id')
    group: fields.ForeignKeyRelation[GroupModel] = fields.ForeignKeyField(model_name='main.GroupModel',
                                                                          to_field='id')

    class Meta:
        """Metaclass to set table name and description"""

        table = "subject"
        table_description = "Stores information about the subject"
        unique_together = (("schedule_id", "employee_id", "number"), ("schedule_id", "group_id", "number"))


class ExamModel(Model):
    id = fields.IntField(pk=True)
    day = fields.IntEnumField(DayType)
    date = fields.IntField()

    name = fields.TextField()
    sub_group = fields.IntField()
    dislocation = fields.TextField()
    number = fields.SmallIntField()
    type = fields.IntEnumField(SubjectType)
    time = fields.TextField()

    zoom_link = fields.TextField(null=True)
    zoom_password = fields.TextField(null=True)

    employee: fields.ForeignKeyRelation[EmployeeModel] = fields.ForeignKeyField(model_name='main.EmployeeModel',
                                                                                related_name='exams',
                                                                                to_field='id')
    group: fields.ForeignKeyRelation[GroupModel] = fields.ForeignKeyField(model_name='main.GroupModel',
                                                                          to_field='id')

    class Meta:
        """Metaclass to set table name and description"""

        table = "exam"
        table_description = "Stores information about the exam"


Faculty = pydantic_model_creator(FacultyModel, name="Faculty")
Department = pydantic_model_creator(DepartmentModel, name="Department")
Group = pydantic_model_creator(GroupModel, name="Group")
Employee = pydantic_model_creator(FacultyModel, name="Employee")
ScheduleSubject = pydantic_model_creator(ScheduleSubjectModel, name="ScheduleSubject")
Exam = pydantic_model_creator(ExamModel, name="Exam")

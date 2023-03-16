import typing
from datetime import datetime

from pydantic import Field, BaseModel, validator

from app.models.enums import (try_value,
                              DayType,
                              EducationalLevel,
                              educational_level_ru,
                              SubjectType,
                              subject_type_ru,
                              )

__all__: typing.Sequence[str] = ("ScheduleEntryHTTP",
                                 "ScheduleHTTP",
                                 "ScheduleDayHTTP",
                                 "StudentGroupHTTP",
                                 "FacultyHTTP",
                                 "EmployeeHTTP",
                                 "DepartmentHTTP",
                                 "ExamHTTP"
                                 )


class ScheduleEntryHTTP(BaseModel):
    id: str = Field(alias="id_cell")
    name: str = Field(alias="TitleSubject")
    type: SubjectType = Field(alias="TypeLesson")
    subject_id: int = Field(alias="idSubject")
    title: str = Field(alias="title")
    department_name: str = Field(alias="special")

    date: int = Field(alias="DateLesson")
    day: DayType = Field(alias="DayWeek")

    sub_group: int = Field(alias="NumberSubGruop")
    building: str = Field(alias='Korpus')
    audience: str = Field(alias="NumberRoom")
    number: int = Field(alias="NumberLesson")

    employee_id: int
    employee_name: str = Field(alias="Name")
    employee_second_name: str = Field(alias="Family")
    employee_middle_name: str = Field(alias='SecondName')

    group_id: int = Field(alias="idGruop")

    zoom_link: typing.Optional[str]
    zoom_password: typing.Optional[str]

    @validator("date", pre=True)
    def parse_date(cls, value):
        return datetime.strptime(value, "%Y-%m-%d").timestamp()

    @validator("day", pre=True)
    def parse_day_week(cls, value):
        return try_value(DayType, value - 1)

    @validator("type", pre=True)
    def parse_type(cls, value):
        return subject_type_ru.get(value)


class ExamHTTP(BaseModel):
    photo_link: str = Field(alias="foto_link")
    id: str = Field(alias="id_cell")
    name: str = Field(alias="TitleSubject")
    type: SubjectType = Field(alias="TypeLesson")

    date: int = Field(alias="DateLesson")
    day: DayType = Field(alias="DayWeek")

    sub_group: int = Field(alias="NumberSubGruop")
    dislocation: str = Field(alias="NumberRoom")
    number: int = Field(alias="NumberLesson")
    time: str = Field(alias="Time")

    employee_id: int
    employee_name: str = Field(alias="Name")
    employee_second_name: str = Field(alias="Family")
    employee_middle_name: str = Field(alias='SecondName')

    group_id: int = Field(alias="idGruop")

    @validator("date", pre=True)
    def parse_date(cls, value):
        return datetime.strptime(value, "%d.%m.%Y").timestamp()

    @validator("day", pre=True)
    def parse_day_week(cls, value):
        return try_value(DayType, value - 1)

    @validator("type", pre=True)
    def parse_type(cls, value):
        return subject_type_ru.get(value)


class ScheduleDayHTTP:
    def __init__(self, date: int, day: DayType, entries: typing.List[ScheduleEntryHTTP]):
        self.day = day
        self.date = date + 86400 * day
        self.subjects: typing.List[ScheduleEntryHTTP] = entries


class ScheduleHTTP:
    def __init__(self, date: int, entries: typing.List[ScheduleEntryHTTP]):
        self.days: dict[DayType, ScheduleDayHTTP] = {day: ScheduleDayHTTP(date, day, []) for day in DayType}

        for entry in entries:
            self.days[entry.day].subjects.append(entry)


class StudentGroupHTTP(BaseModel):
    id: int = Field(alias='idgruop')
    direction: str = Field(alias="Codedirection")
    level: EducationalLevel = Field(alias="levelEducation")
    name: str = Field(alias="title")

    @validator("level", pre=True)
    def parse_level(cls, value):
        return educational_level_ru.get(value)


class FacultyHTTP(BaseModel):
    id: int = Field(alias="idDivision")
    title: str = Field(alias="titleDivision")
    short_title: str = Field(alias="shortTitle")

    def __hash__(self):
        return self.id


class DepartmentHTTP(BaseModel):
    id: int = Field(alias="idDivision")
    title: str = Field(alias="titleDivision")
    short_title: str = Field(alias="shortTitle")

    def __hash__(self):
        return self.id


class EmployeeHTTP(BaseModel):
    id: int = Field(alias="employee_id")
    name: str = Field(alias="Name")
    second_name: str = Field(alias="Family")
    middle_name: str = Field(alias='SecondName')
    full_name: str = Field(alias="fio")

    def __hash__(self):
        return self.id

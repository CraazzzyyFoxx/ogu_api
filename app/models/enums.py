import enum


__all__ = ("UserType",
           "DayType",
           "EducationalLevel",
           "Years",
           "ActionStats",
           "SubjectType",
           "subject_type_ru",
           "educational_level_ru",
           "try_value",
           )


class UserType(enum.IntEnum):
    Student = 0
    Lecturer = 1


class DayType(enum.IntEnum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5


class EducationalLevel(enum.IntEnum):
    Undergraduate = 0
    Specialty = 1
    Magistracy = 2
    Postgraduate = 3
    Residency = 4


class Years(enum.IntEnum):
    First = 1
    Second = 2
    Third = 3
    Fourth = 4
    Fifth = 5


class ActionStats(enum.IntEnum):
    fetch_faculties = 0
    fetch_departments = 1
    fetch_employees = 2
    fetch_groups = 3
    fetch_schedule = 4
    fetch_employee = 5
    fetch_data = 6
    fetch_exams = 7


class SubjectType(enum.IntEnum):
    lecture = 0
    practice = 1
    laboratory = 2
    test = 3
    exam = 4
    consultation = 5


def try_value(cls, value):
    for name, value_ in cls._member_map_.items():
        if value_.value == int(value):
            return cls._member_map_[name]
    return value


subject_type_ru = {
    "лек": SubjectType.lecture,
    "пр": SubjectType.practice,
    "лаб": SubjectType.laboratory,
    "зачет": SubjectType.test,
    "экзамен": SubjectType.exam,
    "консультация": SubjectType.consultation,
}

educational_level_ru = {"бакалавриат": EducationalLevel.Undergraduate,
                        "специалитет": EducationalLevel.Specialty,
                        "магистратура": EducationalLevel.Magistracy,
                        "аспирантура": EducationalLevel.Postgraduate,
                        "ординатура": EducationalLevel.Residency
                        }

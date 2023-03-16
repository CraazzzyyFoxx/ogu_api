import datetime

from pydantic import BaseSettings


class ApiConfig(BaseSettings):
    token: str
    has_display: bool
    chrome_driver_dir: str

    class Config:
        env_file = ".env"
        env_prefix = "api_"


class DatabaseConfig(BaseSettings):
    db: str
    host: str
    password: str
    port: int
    user: str

    class Config:
        env_file = ".env"
        env_prefix = "postgres_"


api = ApiConfig()
# db = DatabaseConfig()

UNABLE_RATE_LIMIT = True

UPDATE_FETCH_SCHEDULE = datetime.timedelta(hours=3)
UPDATE_FETCH_EXAMS = datetime.timedelta(hours=3)
UPDATE_FETCH_FACULTIES = datetime.timedelta(hours=24)
UPDATE_FETCH_DEPARTMENTS = datetime.timedelta(hours=24)
UPDATE_FETCH_EMPLOYEES = datetime.timedelta(hours=24)
UPDATE_FETCH_EMPLOYEE = datetime.timedelta(hours=3)
UPDATE_FETCH_DATA = datetime.timedelta(days=180)

# Constants for calculating time
START_SEMESTER = int(datetime.datetime(2022, 8, 29).timestamp())
BASE_WEEK_DELTA = 0

# tortoise_config = {
#     "connections": {
#         "default": {
#             "engine": "tortoise.backends.asyncpg",
#             "credentials": {
#                 "database": db.db,
#                 "host": db.host,  # db for docker
#                 "password": db.password,
#                 "port": db.port,
#                 "user": db.user,
#             },
#         }
#     },
#     "apps": {
#         "main": {
#             "models": ["app.models.db"],
#             "default_connection": "default",
#         }
#     },
# }

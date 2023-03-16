import time
import typing
import typing as t
from datetime import datetime, timedelta

import httpx
import orjson
import pytz

from urllib.parse import quote
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from loguru import logger

import config
from app.utils.time import ScheduleTime
from app.models.enums import Years
from app.models.db import UserAgentModel, CookieModel

from .models import (ScheduleEntryHTTP,
                     StudentGroupHTTP,
                     FacultyHTTP,
                     DepartmentHTTP,
                     EmployeeHTTP, ScheduleHTTP,
                     ExamHTTP)


async def json_or_text(response: httpx.Response) -> dict | str | None:
    text = response.text
    try:
        if response.headers['content-type'] == 'application/json':
            return orjson.loads(text)
    except KeyError:
        # Thanks Cloudflare
        return None

    return text


class Route:
    BASE: t.ClassVar[str] = 'https://oreluniver.ru'

    def __init__(self, method: str, path: str, **parameters: t.Any) -> None:
        self.path: str = path
        self.method: str = method
        url = self.BASE + self.path
        if parameters:
            url = url.format_map({k: quote(v) if isinstance(v, str) else v for k, v in parameters.items()})
        self.url: str = url


class HTTPClient:
    """Represents an HTTP client sending HTTP requests to the oreluniver.ru"""

    __slots__ = ("_client", "_client_kwargs", "user_agent", "cookie")

    def __init__(self):
        limits = httpx.Limits(
            max_connections=20,
            max_keepalive_connections=10,
        )

        self._client_kwargs = dict(  # pylint: disable=use-dict-literal
            limits=limits,
            http1=True,
        )

        self._client = self._build_client()
        self.user_agent: t.Optional[str] = ""
        self.cookie: t.Optional[str] = ""

    def _build_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(**self._client_kwargs)  # type: ignore[arg-type]

    async def initialize(self) -> None:
        if self._client.is_closed:
            self._client = self._build_client()

    async def shutdown(self) -> None:
        if self._client.is_closed:
            logger.debug("This HTTPXRequest is already shut down. Returning.")
            return

        await self._client.aclose()

    async def request(self, route: Route) -> t.Any:
        url = route.url
        method = route.method

        if self._client.is_closed:
            raise RuntimeError("This HTTPXRequest is not initialized!")

        for tries in range(5):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    headers={"User-Agent": self.user_agent, "cookie": self.cookie},
                )
            except httpx.TimeoutException as err:
                raise err
            except httpx.HTTPError as err:
                raise err

            data = await json_or_text(response)
            logger.error(response.text)

            if data is not None:
                return data

            await self.update_cookies()

    async def update_cookies(self):
        user_agent = await UserAgentModel.filter().order_by("-datetime").first()
        if user_agent and user_agent.datetime > (datetime.utcnow() - timedelta(minutes=1)).astimezone(pytz.utc):
            pass

        chrome_options = webdriver.ChromeOptions()
        ua = UserAgent()
        chrome_options.add_argument(f'user-agent={self.user_agent}')
        self.user_agent = ua.chrome
        chrome_options.add_argument("--start-maximized")  # open Browser in maximized mode
        chrome_options.add_argument("--no-sandbox")  # bypass OS security model
        chrome_options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        s = Service(executable_path=config.api.chrome_driver_dir)
        driver = webdriver.Chrome(service=s, options=chrome_options)
        try:
            logger.info("Fetching cookies for user-agent {}", self.user_agent)
            driver.get(Route.BASE)
            time.sleep(5)
            cookie_btn = driver.find_element(By.XPATH, '/html/body/div[6]/div/div/div/div')
            cookie_btn.click()
            cookies = driver.get_cookies()
            logger.info("Fetched cookies {}", cookies)
            self.cookie = " ".join(f'{cookie.get("name")}={cookie.get("value")};' for cookie in cookies)

            await UserAgentModel.create(extra=self.user_agent, datetime=datetime.utcnow())
            await CookieModel.create(extra=self.cookie, datetime=datetime.utcnow())

        except Exception as ex:
            logger.error(ex)
        finally:
            driver.close()
            driver.quit()

    async def get_schedule_student(self, group_id: int, week_delta: int = 0) -> t.Optional[ScheduleHTTP]:
        timestamp = ScheduleTime.compute_timestamp_for_api(week_delta)
        route = Route('GET', '/schedule//{group_id}///{timestamp}/printschedule',
                      group_id=group_id,
                      timestamp=timestamp)
        data: dict = await self.request(route)
        if not data:
            return
        schedule = ScheduleHTTP(ScheduleTime.compute_timestamp(week_delta=week_delta),
                                sorted([ScheduleEntryHTTP.parse_obj(raw) for index, raw in data.items()
                                        if index.isdigit()],
                                       key=lambda x: x.date))
        return schedule

    async def get_schedule_employee(self, employee_id: int, week_delta: int = 0) -> t.Optional[ScheduleHTTP]:
        timestamp = ScheduleTime.compute_timestamp_for_api(week_delta=week_delta)
        route = Route('GET', '/schedule/{employee_id}////{timestamp}/printschedule',
                      employee_id=employee_id,
                      timestamp=timestamp)
        data: dict = await self.request(route)
        if not data:
            return
        return ScheduleHTTP(ScheduleTime.compute_timestamp(week_delta=week_delta),
                            sorted([ScheduleEntryHTTP.parse_obj(raw) for index, raw in data.items()
                                    if index.isdigit()],
                                   key=lambda x: x.date))

    async def get_groups(self, faculty_id: int, course: Years) -> t.List[StudentGroupHTTP]:
        route = Route('GET', '/schedule/{faculty_id}/{course}/grouplist', faculty_id=faculty_id, course=course.value)
        data: dict = await self.request(route)
        return [StudentGroupHTTP.parse_obj(raw) for raw in data]

    async def get_faculties(self) -> t.List[FacultyHTTP]:
        route = Route('GET', '/schedule/divisionlistforstuds')
        data = await self.request(route)
        return [FacultyHTTP.parse_obj(raw) for raw in data]

    async def get_departments(self, faculty_id: int) -> t.List[DepartmentHTTP]:
        route = Route('GET', '/schedule/{faculty_id}/kaflist', faculty_id=faculty_id)
        data: dict = await self.request(route)
        return [DepartmentHTTP.parse_obj(raw) for raw in data]

    async def get_employees(self, department_id: int) -> t.List[EmployeeHTTP]:
        route = Route('GET', '/schedule/{department_id}/preplist',
                      department_id=department_id)
        data: dict = await self.request(route)
        return [EmployeeHTTP.parse_obj(raw) for raw in data]

    async def get_employee(self, employee_id: int) -> EmployeeHTTP:
        route = Route('GET', '/employee/{employee_id}', employee_id=employee_id)
        data: dict = await self.request(route)
        return EmployeeHTTP.parse_obj(data)

    async def get_exams_student(self, group_id: int) -> typing.List[ExamHTTP]:
        route = Route('GET', '/schedule/{group_id}////printexamschedule', group_id=group_id)
        data: dict = await self.request(route)
        return sorted([ExamHTTP.parse_obj(raw) for raw in data],
                      key=lambda x: x.time)

    async def get_exams_employee(self, employee_id: int) -> typing.List[ExamHTTP]:
        route = Route('GET', '/schedule//{employee_id}///printexamschedule', employee_id=employee_id)
        data: dict = await self.request(route)
        return sorted([ExamHTTP.parse_obj(raw) for raw in data],
                      key=lambda x: x.time)

from fastapi import APIRouter, Depends

from app.models.db import Faculty, FacultyModel, DepartmentModel, Department, GroupModel, Group, EmployeeModel, Employee
from app.services.auth import AuthService

router = APIRouter(prefix="/api/v1", dependencies=[Depends(AuthService.requires_authorization)])


@router.get("/faculties", response_model=list[Faculty])
async def get_faculties():
    return await Faculty.from_queryset(FacultyModel.all())


@router.get("/department/{faculty_id}", response_model=list[Department])
async def get_departments(faculty_id: int):
    return await Department.from_queryset(DepartmentModel.filter(faculty_id=faculty_id))


@router.get("/employee/{department_id}", response_model=list[Employee])
async def get_employees(department_id: int):
    return await Employee.from_queryset(EmployeeModel.filter(department_id=department_id))


@router.get("/group/{faculty_id}", response_model=list[Group])
async def get_groups(faculty_id: int):
    return await Group.from_queryset(GroupModel.filter(faculty_id=faculty_id))

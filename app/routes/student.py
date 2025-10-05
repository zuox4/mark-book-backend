import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from fastapi import APIRouter, Depends, HTTPException

from app.database.models import User, ProjectOffice, Group

from app.auth.dependencies import get_current_active_user, get_current_user
from app.services.SchoolServices import SchoolService


router = APIRouter()

class ProjectResponse(BaseModel):
    title: str
    description: str
    logo_url: str


@router.get("/", response_model=dict)
async def get_student_info(current_user: User = Depends(get_current_active_user),  db: Session = Depends(get_db)):
    student = SchoolService().get_student_data(current_user.external_id)
    print(student.className)
    projects_office = db.query(ProjectOffice).join(ProjectOffice.accessible_classes).filter(Group.name==student.className).first()
    return {'display_name': student.display_name, 'class_name': student.className, "project_office_id": projects_office.id if projects_office else None}


@router.get("/project_office", response_model=ProjectResponse)
async def get_project_office_info(current_user: User = Depends(get_current_active_user),  db: Session = Depends(get_db)):
    student = SchoolService().get_student_data(current_user.external_id)
    print(student.className)
    projects_office = db.query(ProjectOffice).join(ProjectOffice.accessible_classes).filter(Group.name==student.className).first()
    if projects_office is None:
        raise HTTPException(status_code=404, detail=str('Проект для пользователя не найден'))

    return projects_office

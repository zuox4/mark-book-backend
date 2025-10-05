import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from fastapi import APIRouter, Depends, HTTPException

from app.database.models import User, ProjectOffice, Group

from app.auth.dependencies import get_current_active_user, get_current_user
from app.routes.mark_book import RecordBookResponse, get_student_record_book_marks_simple
from app.services.SchoolServices import SchoolService


router = APIRouter()

class Event(BaseModel):
    id: int
    title: str

class ProjectOfficeResponse(BaseModel):
    title: str
    description: str
    logo_url: str
    accessible_events: List[Event]

class GroupLeaderResponse(BaseModel):
    display_name: str
    about: Optional[str] = None
    image: Optional[str] = None
    email: Optional[str] = None
    max_url: Optional[str] = None


class StudentInfoResponse(BaseModel):
    display_name: str
    class_name: str
    project_office_id: Optional[int] = None
    group_leader: Optional[GroupLeaderResponse] = None
    project_leader: Optional[GroupLeaderResponse] = None



@router.get("/", response_model=StudentInfoResponse)
def get_student_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> StudentInfoResponse:
    student = SchoolService().get_student_data(current_user.external_id)

    projects_office = db.query(ProjectOffice) \
        .join(ProjectOffice.accessible_classes) \
        .filter(Group.name == student.className) \
        .first()

    if projects_office:

        project_leader = projects_office.leader
    else:
        project_leader =None
    project_leader_response=None
    if project_leader:
        project_leader_response = GroupLeaderResponse(
            display_name=project_leader.display_name,
            about=project_leader.about,
            image=project_leader.image,
            max_url=project_leader.max_link_url,
            email=project_leader.email,
        )

    group_leader = SchoolService().get_group_leader_by_class_name('7-Т')

    # Обработка классного руководителя
    group_leader_response = None
    if group_leader:

        leader_info = db.query(User).filter(User.external_id == group_leader.uid).first()

        group_leader_response = GroupLeaderResponse(
            display_name=leader_info.display_name if leader_info else group_leader.display_name,
            about=leader_info.about if leader_info else None,
            image=leader_info.image if leader_info else group_leader.image,
            max_url=leader_info.max_link_url if leader_info else None,
            email=leader_info.email if leader_info else group_leader.email,
        )

    return StudentInfoResponse(
        display_name=student.display_name,
        class_name=student.className,
        project_office_id=projects_office.id if projects_office else None,
        group_leader=group_leader_response,
        project_leader=project_leader_response,
    )


@router.get("/project_office", response_model=ProjectOfficeResponse)
async def get_project_office_info(current_user: User = Depends(get_current_active_user),  db: Session = Depends(get_db)):
    student = SchoolService().get_student_data(current_user.external_id)
    print(student.className)

    projects_office = db.query(ProjectOffice).join(ProjectOffice.accessible_classes).filter(Group.name==student.className).first()

    if projects_office is None:
        raise HTTPException(status_code=404, detail=str('Проект для пользователя не найден'))

    return projects_office


@router.get("/record-book/marks", response_model=RecordBookResponse)
async def get_record_book_marks(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Получаем класс студента
    student_data = SchoolService().get_student_data(current_user.external_id)
    student_class = student_data.className

    return get_student_record_book_marks_simple(db, current_user.external_id, student_class)
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from app.database.models import *
from app.database.models.associations import p_office_event_association, p_office_group_association


class StageMark(BaseModel):
    name: str
    status: str  # "зачет" или "незачет"
    date: Optional[str] = None
    result_title: Optional[str] = None  # Название результата
    score: Optional[int] = None  # Баллы за этап


class EventMark(BaseModel):
    id: int
    eventName: str
    type: str  # "зачет" или "незачет" - на основе всех этапов
    date: str
    stages: List[StageMark]
    total_score: Optional[int] = 0  # Общая сумма баллов за мероприятие


class RecordBookResponse(BaseModel):
    marks: List[EventMark]


from sqlalchemy.orm import Session


def get_student_record_book_marks_simple(
        db: Session,
        student_external_id: str,
        student_class: str
) -> RecordBookResponse:
    # Получаем все доступные мероприятия для класса
    accessible_events = (
        db.query(Event)
        .join(p_office_event_association, Event.id == p_office_event_association.c.event_id)
        .join(ProjectOffice, p_office_event_association.c.p_office_id == ProjectOffice.id)
        .join(p_office_group_association, ProjectOffice.id == p_office_group_association.c.p_office_id)
        .join(Group, p_office_group_association.c.group_id == Group.id)
        .filter(Group.name == student_class)
        .filter(Event.is_active == True)
        .all()
    )

    marks = []

    for event in accessible_events:
        # Получаем все этапы для этого типа мероприятия
        stages = (
            db.query(Stage)
            .filter(Stage.event_type_id == event.event_type_id)
            .all()
        )

        event_stages = []
        all_stages_completed = True
        total_event_score = 0

        for stage in stages:
            # Проверяем, есть ли достижения у студента для этого этапа
            achievement = (
                db.query(Achievement)
                .join(PossibleResult, Achievement.result_id == PossibleResult.id)
                .filter(
                    Achievement.student_external_id == student_external_id,
                    Achievement.event_id == event.id,
                    Achievement.stage_id == stage.id
                )
                .first()
            )

            if achievement:
                stage_status = "зачет"
                stage_date = achievement.achieved_at.isoformat()
                result_title = achievement.result.title if achievement.result else None
                score = stage.score_for_finish if stage.score_for_finish else 0
                total_event_score += score
            else:
                stage_status = "незачет"
                stage_date = None
                result_title = None
                score = 0
                all_stages_completed = False

            event_stages.append(StageMark(
                name=stage.title,
                status=stage_status,
                date=stage_date,
                result_title=result_title,
                score=score if achievement else None
            ))

        event_status = "зачет" if all_stages_completed and stages else "незачет"

        marks.append(EventMark(
            id=event.id,
            eventName=event.title,
            type=event_status,
            date=event.date_start.isoformat() if event.date_start else "2024-01-01",
            stages=event_stages,
            total_score=total_event_score
        ))

    return RecordBookResponse(marks=marks)



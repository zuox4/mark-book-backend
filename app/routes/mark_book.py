from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database.models import *

class StageMark(BaseModel):
    name: str
    status: str  # "зачет" или "незачет"
    date: Optional[str] = None
    result_title: Optional[str] = None  # Название результата
    score: Optional[int] = None  # Баллы за этап
    min_required_score: int  # Минимальное количество баллов для зачета
    current_score: int  # Текущее количество баллов


class EventMark(BaseModel):
    id: int
    eventName: str
    type: str  # "зачет" или "незачет" - на основе всех этапов
    date: str
    stages: List[StageMark]
    total_score: Optional[int] = 0  # Общая сумма баллов за мероприятие
    min_stages_required: int  # Минимальное количество этапов для завершения
    completed_stages_count: int  # Количество завершенных этапов


class RecordBookResponse(BaseModel):
    marks: List[EventMark]


def get_student_record_book_marks_simple(
        db: Session,
        student_id: int,  # Изменено с student_external_id на student_id
        student_class: str
) -> RecordBookResponse:
    # Получаем пользователя
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        return RecordBookResponse(marks=[])

    # Получаем все доступные мероприятия для класса через проектные офисы
    accessible_events = (
        db.query(Event)
        .join(p_office_event_association, Event.id == p_office_event_association.c.event_id)
        .join(ProjectOffice, p_office_event_association.c.p_office_id == ProjectOffice.id)
        .join(p_office_group_association, ProjectOffice.id == p_office_group_association.c.p_office_id)
        .join(Group, p_office_group_association.c.group_id == Group.id)
        .filter(Group.name == student_class)
        .filter(Event.is_active == True)
        .filter(ProjectOffice.is_active == True)
        .all()
    )

    marks = []

    for event in accessible_events:
        # Получаем тип мероприятия для доступа к этапам
        event_type = event.event_type

        # Получаем все этапы для этого типа мероприятия
        stages = (
            db.query(Stage)
            .filter(Stage.event_type_id == event.event_type_id)
            .order_by(Stage.stage_order)
            .all()
        )

        event_stages = []
        completed_stages_count = 0
        total_event_score = 0

        for stage in stages:
            # Получаем ВСЕ достижения студента для этого этапа (может быть несколько)
            achievements = (
                db.query(Achievement)
                .join(PossibleResult, Achievement.result_id == PossibleResult.id)
                .filter(
                    Achievement.student_id == student_id,
                    Achievement.event_id == event.id,
                    Achievement.stage_id == stage.id
                )
                .all()
            )

            # Считаем общие баллы за этап
            stage_total_score = sum(achievement.result.points_for_done for achievement in achievements)
            total_event_score += stage_total_score

            # Определяем статус этапа
            is_stage_completed = stage_total_score >= stage.min_score_for_finished

            if is_stage_completed:
                completed_stages_count += 1

            # Получаем последнее достижение для даты и названия
            last_achievement = achievements[-1] if achievements else None

            event_stages.append(StageMark(
                name=stage.title,
                status="зачет" if is_stage_completed else "незачет",
                date=last_achievement.achieved_at.isoformat() if last_achievement else None,
                result_title=last_achievement.result.title if last_achievement else None,
                score=stage_total_score,
                min_required_score=stage.min_score_for_finished,
                current_score=stage_total_score
            ))

        # Определяем статус всего мероприятия
        min_stages_required = event_type.min_stages_for_completion or 0
        is_event_completed = completed_stages_count >= min_stages_required

        event_status = "зачет" if is_event_completed and stages else "незачет"

        # Определяем дату мероприятия
        event_date = (
            event.date_start.isoformat() if event.date_start else
            event.date_end.isoformat() if event.date_end else
            datetime.now().isoformat()
        )

        marks.append(EventMark(
            id=event.id,
            eventName=event.title,
            type=event_status,
            date=event_date,
            stages=event_stages,
            total_score=total_event_score,
            min_stages_required=min_stages_required,
            completed_stages_count=completed_stages_count
        ))

    return RecordBookResponse(marks=marks)
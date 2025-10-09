from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import APIRouter, Depends, HTTPException,Query
from typing import List

from ..auth.dependencies import get_current_active_user
from ..database import get_db
from app.database.models import User, Event, ProjectOffice, EventType, Stage, Achievement, PossibleResult, Group, \
    p_office_group_association, p_office_event_association
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class StageResultResponse(BaseModel):
    name: str
    status: str
    date: Optional[datetime]
    result_title: Optional[str]
    score: int
    min_required_score: int
    current_score: int
    stage_id: int
    possible_results: List[dict]

class ProjectOfficeJournalResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    group_name: str  # Новое поле - название класса
    class_teacher: Optional[str] = None  # Классный руководитель
    event_name: str
    type: str
    date: datetime
    stages: List[StageResultResponse]
    total_score: int
    min_stages_required: int
    completed_stages_count: int

    class Config:
        from_attributes = True

router = APIRouter()

@router.get("/journal/{event_id}", response_model=List[ProjectOfficeJournalResponse])
def get_project_office_journal(
        event_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Получить журнал по мероприятию для проектного офиса (классы проектного офиса)
    """
    # Проверяем существование мероприятия
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    # Проверяем, что мероприятие относится к проектному офису пользователя
    project_office = db.query(ProjectOffice).filter(
        ProjectOffice.leader_uid == current_user.id
    ).first()

    if not project_office:
        raise HTTPException(status_code=404, detail="Проектный офис не найден")

    # Проверяем, что мероприятие привязано к проектному офису
    event_in_office = db.query(p_office_event_association).filter(
        and_(
            p_office_event_association.c.p_office_id == project_office.id,
            p_office_event_association.c.event_id == event_id
        )
    ).first()

    if not event_in_office:
        raise HTTPException(status_code=403, detail="Мероприятие не доступно для вашего проектного офиса")

    # Получаем тип мероприятия и его стадии
    event_type = db.query(EventType).filter(EventType.id == event.event_type_id).first()
    stages = db.query(Stage).filter(
        Stage.event_type_id == event.event_type_id
    ).order_by(Stage.stage_order).all()

    # Получаем классы, привязанные к проектному офису
    office_groups = db.query(Group).join(
        p_office_group_association,
        p_office_group_association.c.group_id == Group.id
    ).filter(
        p_office_group_association.c.p_office_id == project_office.id
    ).all()

    if not office_groups:
        raise HTTPException(status_code=404, detail="Нет доступных классов в проектном офисе")

    result = []

    for group in office_groups:
        # Получаем всех учеников класса
        students = db.query(User).filter(
            User.group_name == group.name,
            User.archived == False,
        ).all()

        for student in students:
            student_data = {
                "id": student.id,
                "student_id": student.id,
                "student_name": student.display_name or f"Ученик {student.id}",
                "group_name": group.name,
                "class_teacher": group.leader_name if hasattr(group, 'leader_name') else None,
                "event_name": event.title,
                "type": event_type.title,
                "date": event.date_start or datetime.utcnow(),
                "stages": [],
                "total_score": 0,
                "min_stages_required": event_type.min_stages_for_completion or len(stages),
                "completed_stages_count": 0
            }

            total_score = 0
            completed_stages = 0

            for stage in stages:
                # Получаем возможные результаты для стадии
                possible_results = db.query(PossibleResult).filter(
                    PossibleResult.stage_id == stage.id
                ).all()

                # Ищем достижение ученика для этой стадии
                achievement = db.query(Achievement).filter(
                    and_(
                        Achievement.student_id == student.id,
                        Achievement.event_id == event_id,
                        Achievement.stage_id == stage.id
                    )
                ).first()

                current_score = 0
                result_title = None
                status = "незачет"

                if achievement:
                    # Если есть достижение, берем баллы и название результата
                    current_score = achievement.result.points_for_done
                    result_title = achievement.result.title

                    # Проверяем удовлетворяет ли результат минимальным требованиям
                    if current_score >= stage.min_score_for_finished:
                        status = "зачет"
                        completed_stages += 1
                    else:
                        status = "незачет"
                else:
                    # Если достижения нет
                    status = "незачет"
                    current_score = 0

                total_score += current_score

                stage_data = StageResultResponse(
                    name=stage.title,
                    status=status,
                    date=achievement.achieved_at if achievement else None,
                    result_title=result_title,
                    score=stage.min_score_for_finished,
                    min_required_score=stage.min_score_for_finished,
                    current_score=current_score,
                    stage_id=stage.id,
                    possible_results=[
                        {
                            "id": pr.id,
                            "title": pr.title,
                            "points": pr.points_for_done
                        } for pr in possible_results
                    ]
                )

                student_data["stages"].append(stage_data)

            student_data["total_score"] = total_score
            student_data["completed_stages_count"] = completed_stages
            result.append(ProjectOfficeJournalResponse(**student_data))

    # Сортируем результат по классам и именам учеников для удобства
    result.sort(key=lambda x: (x.group_name, x.student_name))

    return result


@router.get("/events")
def get_project_office_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить список мероприятий доступных для проектного офиса
    """
    # Получаем проектный офис пользователя
    project_office = db.query(ProjectOffice).filter(
        ProjectOffice.leader_uid == current_user.id
    ).first()

    if not project_office:
        raise HTTPException(status_code=404, detail="Проектный офис не найден")

    # Получаем мероприятия, привязанные к проектному офису
    events = db.query(Event).join(
        p_office_event_association,
        p_office_event_association.c.event_id == Event.id
    ).filter(
        and_(
            p_office_event_association.c.p_office_id == project_office.id,
            Event.is_active == True
        )
    ).order_by(Event.date_start.desc()).all()

    return [
        {
            "id": event.id,
            "title": event.title,
            "date_start": event.date_start,
            "date_end": event.date_end,
            "event_type": event.event_type.title,
            "description": event.description
        }
        for event in events
    ]


@router.get("/groups")
def get_project_office_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить список классов под управлением проектного офиса
    """
    # Получаем проектный офис пользователя
    project_office = db.query(ProjectOffice).filter(
        ProjectOffice.leader_uid == current_user.id
    ).first()

    if not project_office:
        raise HTTPException(status_code=404, detail="Проектный офис не найден")

    # Получаем классы, привязанные к проектному офису
    groups = db.query(Group).join(
        p_office_group_association,
        p_office_group_association.c.group_id == Group.id
    ).filter(
        p_office_group_association.c.p_office_id == project_office.id
    ).order_by(Group.name).all()

    return [
        {
            "id": group.id,
            "name": group.name,
            "student_count": db.query(User).filter(
                User.group_name == group.name,
                User.archived == False
            ).count(),
            "leader_name": group.leader_name if hasattr(group, 'leader_name') else None
        }
        for group in groups
    ]


@router.get("/stats/{event_id}")
def get_project_office_event_stats(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить расширенную статистику по мероприятию для проектного офиса
    """
    # Используем основной эндпоинт для получения данных
    journal_data = get_project_office_journal(event_id, db, current_user)

    # Агрегируем статистику
    total_students = len(journal_data)
    groups = set(item.group_name for item in journal_data)

    # Статистика по классам
    group_stats = []
    for group_name in groups:
        group_students = [s for s in journal_data if s.group_name == group_name]
        completed = len([s for s in group_students if s.completed_stages_count >= s.min_stages_required])

        group_stats.append({
            "group_name": group_name,
            "total_students": len(group_students),
            "completed_students": completed,
            "completion_rate": (completed / len(group_students)) * 100 if group_students else 0,
            "average_score": sum(s.total_score for s in group_students) / len(group_students) if group_students else 0
        })

    # Общая статистика
    total_completed = len([s for s in journal_data if s.completed_stages_count >= s.min_stages_required])
    average_score = sum(s.total_score for s in journal_data) / total_students if total_students else 0

    return {
        "event_id": event_id,
        "total_students": total_students,
        "total_groups": len(groups),
        "total_completed": total_completed,
        "completion_rate": (total_completed / total_students) * 100 if total_students else 0,
        "average_score": average_score,
        "group_stats": group_stats
    }


@router.get("/pivot-data")
def get_project_office_pivot_data(
        groups: List[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    print("sdcsdc")
    """
    Получить сводные данные по всем мероприятиям для проектного офиса
    """
    # Получаем проектный офис пользователя
    project_office = db.query(ProjectOffice).filter(
        ProjectOffice.leader_uid == current_user.id
    ).first()

    if not project_office:
        raise HTTPException(status_code=404, detail="Проектный офис не найден")

    # Получаем мероприятия проектного офиса
    office_events = db.query(Event).join(
        p_office_event_association,
        p_office_event_association.c.event_id == Event.id
    ).filter(
        p_office_event_association.c.p_office_id == project_office.id,
        Event.is_active == True
    ).all()

    # Получаем классы проектного офиса (с фильтром если указан)
    office_groups_query = db.query(Group).join(
        p_office_group_association,
        p_office_group_association.c.group_id == Group.id
    ).filter(
        p_office_group_association.c.p_office_id == project_office.id
    )

    # ВАЖНО: Правильно применяем фильтр по классам
    if groups:
        office_groups_query = office_groups_query.filter(Group.name.in_(groups))

    office_groups = office_groups_query.all()

    # Если указаны группы, но ничего не найдено - возвращаем пустой список
    if groups and not office_groups:
        return []

    result = []

    for group in office_groups:
        students = db.query(User).filter(
            User.group_name == group.name,
            User.archived == False,
        ).all()

        for student in students:
            student_data = {
                "id": student.id,
                "student_name": student.display_name or f"Ученик {student.id}",
                "group_name": group.name,
                "class_teacher": group.leader_name if hasattr(group, 'leader_name') else None,
                "events": {}
            }

            # Для каждого мероприятия собираем результаты студента
            for event in office_events:
                event_data = {
                    "event_name": event.title,
                    "total_score": 0,
                    "completed_stages_count": 0,
                    "min_stages_required": 0,
                    "stages": []
                }

                # Получаем стадии мероприятия
                stages = db.query(Stage).filter(
                    Stage.event_type_id == event.event_type_id
                ).order_by(Stage.stage_order).all()

                event_type = db.query(EventType).filter(
                    EventType.id == event.event_type_id
                ).first()

                event_data["min_stages_required"] = event_type.min_stages_for_completion or len(stages)

                total_score = 0
                completed_stages = 0

                for stage in stages:
                    achievement = db.query(Achievement).filter(
                        and_(
                            Achievement.student_id == student.id,
                            Achievement.event_id == event.id,
                            Achievement.stage_id == stage.id
                        )
                    ).first()

                    current_score = 0
                    status = "незачет"

                    if achievement:
                        current_score = achievement.result.points_for_done
                        if current_score >= stage.min_score_for_finished:
                            status = "зачет"
                            completed_stages += 1
                        else:
                            status = "незачет"

                    total_score += current_score

                    event_data["stages"].append({
                        "name": stage.title,
                        "status": status,
                        "current_score": current_score
                    })

                event_data["total_score"] = total_score
                event_data["completed_stages_count"] = completed_stages

                # Определяем общий статус мероприятия
                if completed_stages >= event_data["min_stages_required"]:
                    event_data["status"] = "зачет"
                elif total_score > 0:
                    event_data["status"] = "в процессе"
                else:
                    event_data["status"] = "не начато"

                student_data["events"][str(event.id)] = event_data

            result.append(student_data)
    print(result)
    return result
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request
from app.database.database import engine
from app.database.models.users import User
from app.database.models.roles import Role
from app.database.models.events import Event
from app.database.models.project_offices import ProjectOffice
from app.database.models.groups import Group
from app.database.models.event_types import EventType
from app.database.models.event_types import Stage
from app.database.models.event_types import PossibleResult
from app.database.models.achievements import Achievement


# Простая аутентификация для админки
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        # Временные креды - замените на свои!
        if username == "admin" and password == "admin123":
            request.session.update({"token": "admin-token"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        return token == "admin-token"


# Админка для пользователей
class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

    column_list = [User.id, User.external_id, User.email, User.display_name, User.is_active]
    column_searchable_list = [User.email, User.display_name]
    column_sortable_list = [User.id, User.email]
    form_columns = [
        User.email,
        User.display_name,
        User.external_id,
        User.is_active,
        User.about,
        User.roles,
    ]


# Админка для ролей
class RoleAdmin(ModelView, model=Role):
    name = "Роль"
    name_plural = "Роли"
    icon = "fa-solid fa-users"

    column_list = [Role.id, Role.name, Role.description]
    column_searchable_list = [Role.name]


# Админка для ролей
class PossibleResultsAdmin(ModelView, model=PossibleResult):
    name = "Возможные результаты"
    name_plural = "Возможные результаты"
    icon = "fa-solid fa-users"

    column_list = [
        PossibleResult.id,
        PossibleResult.title,
        PossibleResult.stage,
    ]


# Админка для событий
class EventAdmin(ModelView, model=Event):
    name = "Событие"
    name_plural = "События"
    icon = "fa-solid fa-calendar"

    column_list = [Event.id, Event.title, Event.academic_year, Event.is_active]
    column_searchable_list = [Event.title]
    form_columns = [
        Event.title,
        Event.event_type,
        Event.academic_year,
        Event.date_start,
        Event.date_end,
        Event.is_active,
    ]


# Админка для проектных офисов
class ProjectOfficeAdmin(ModelView, model=ProjectOffice):
    name = "Проектный офис"
    name_plural = "Проектные офисы"
    icon = "fa-solid fa-building"

    column_list = [ProjectOffice.id, ProjectOffice.title, ProjectOffice.is_active]
    column_searchable_list = [ProjectOffice.title]


# Админка для групп
class GroupAdmin(ModelView, model=Group):
    name = "Группа"
    name_plural = "Группы"
    icon = "fa-solid fa-users"

    column_list = [Group.id, Group.name]


# Админка для типов событий
class EventTypeAdmin(ModelView, model=EventType):
    name = "Тип события"
    name_plural = "Типы событий"
    icon = "fa-solid fa-tags"

    column_list = [EventType.id, EventType.title]


# Админка для этапов
class StageAdmin(ModelView, model=Stage):
    name = "Этап"
    name_plural = "Этапы"
    icon = "fa-solid fa-stairs"

    column_list = [Stage.id, Stage.title, Stage.score_for_finish]


# Админка для достижений
class StudentAchievementAdmin(ModelView, model=Achievement):
    name = "Достижение"
    name_plural = "Достижения"
    icon = "fa-solid fa-trophy"

    column_list = [
        Achievement.id,
        Achievement.teacher_id,
        Achievement.achieved_at,
    ]
    form_columns = [
        Achievement.teacher,
        Achievement.student_external_id,
        Achievement.event,
    ]


# Функция настройки админки
def setup_admin(app):
    authentication_backend = AdminAuth(secret_key="your-secret-key-here")
    admin = Admin(
        app,
        engine,
        authentication_backend=authentication_backend,
        title="Админка Educational Platform",
    )

    # Регистрируем все модели
    admin.add_view(UserAdmin)
    admin.add_view(RoleAdmin)
    admin.add_view(EventAdmin)
    admin.add_view(ProjectOfficeAdmin)
    admin.add_view(GroupAdmin)
    admin.add_view(EventTypeAdmin)
    admin.add_view(StageAdmin)
    admin.add_view(StudentAchievementAdmin)
    admin.add_view(PossibleResultsAdmin)

    return admin

import os
import time

from mysql import connector
from src.app.user.unit_of_work import UserUnitOfWork
from src.app.game.service import GameService
from src.app.role.models import UserRoleEnum
from src.app.role.service import RoleService
from src.app.role.unit_of_work import RoleUnitOfWork
from src.app.user.service import UserSchema, UserService
from src.core.config import QUERIES, Config, Enviroment, Settings

from .database import Database


def startup_db_with_connector(settings: Settings):
    parameters = Config.CONNECTION_URL.translate_connect_args()
    del parameters["database"]

    is_connected = False
    count = 1
    while not is_connected:
        try:
            cnx = connector.connect(**parameters)
            is_connected = cnx.is_connected()
        except connector.errors.Error as err:
            print(err)
            print(f"Trying to reconnect...Attempt №{count}")
            time.sleep(3)
            count += 1
            if count > 25:
                raise connector.errors.DatabaseError("Too many attempts, try later ^_^")

    # создать схему в базе данных, если её нет
    cnx = connector.connect(**parameters)
    cnx.start_transaction()
    cursor = cnx.cursor()

    if settings.ENVIROMENT != Enviroment.Production:
        if settings.DROP_BEFORE:
            cursor.execute(
                f"drop database if exists {Config.CONNECTION_URL.database.lower()}"
            )
        cursor.execute(
            f"create database if not exists {Config.CONNECTION_URL.database.lower()} \
                    default character set {QUERIES.charset.lower()}"
        )
    cursor.close()
    cnx.commit()
    cnx.close()


async def startup_db_with_engine(settings: Settings):
    # обновляем схему БД до последнего коммита
    os.system("alembic current")
    os.system("alembic upgrade head")

    # создаем необходимые экземпляры зависимостей
    db_session = Database.SessionLocal()
    role_uow = RoleUnitOfWork(db_session)
    user_uow = UserUnitOfWork(db_session)
    game_service = GameService()

    # отправляем запрос на игровой сервер, чтобы получить базовые роли и их кастомные настройки
    await game_service.write_gamecore_settings_list_to_database(
        role_uow, 
        user_uow, 
        settings
    )

    # автоматическое создание чего-либо не должно быть при PRODUCTION
    if (
        settings.ENVIROMENT == Enviroment.Development
        or settings.ENVIROMENT == Enviroment.Testing
    ):
        role_service = RoleService()
        user_service = UserService()

        await role_service.create_required_roles(RoleUnitOfWork(db_session))

        admin_schema = UserSchema(
            login="admin",
            password="admin",
            first_name="admin",
            patronymic="admin",
            last_name="admin",
            city="Saint-Petersburg",
            organization="Geoscan",
            role_name=UserRoleEnum.AdminRole.name,
        )
        users_admin = await user_service.get_users_with_parameters(
            user_uow=user_uow,
            login=admin_schema.login,
            first_name=admin_schema.first_name,
            patronymic=admin_schema.patronymic,
            last_name=admin_schema.patronymic,
            organization=admin_schema.organization,
            city=admin_schema.city,
        )

        if not users_admin:
            await user_service.register_user(user_uow, admin_schema)

        anonym_user_schema = UserSchema(
            login="anonymous",
            password="anonymous",
            first_name="anonymous",
            patronymic="anonymous",
            last_name="anonymous",
            city="Saint-Petersburg",
            organization="Geoscan",
            role_name=UserRoleEnum.AnonymRole.name,
        )
        users_anonym = await user_service.get_users_with_parameters(
            user_uow=user_uow,
            login=anonym_user_schema.login,
            first_name=anonym_user_schema.first_name,
            patronymic=anonym_user_schema.patronymic,
            last_name=anonym_user_schema.last_name,
            organization=anonym_user_schema.organization,
            city=anonym_user_schema.city,
        )
        if not users_anonym:
            await user_service.register_user(user_uow, anonym_user_schema)

    await db_session.commit()
    await db_session.flush()
    await db_session.close()


async def database_startup(settings: Settings):
    startup_db_with_connector(settings)
    await startup_db_with_engine(settings)

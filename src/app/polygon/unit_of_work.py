from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.polygon.request import (
    CreatePolygonConfigRequest,
    ReplacePolygonConfigWithObjectsRequest,
)
from src.app.all_models import PolygonConfig, PolygonObject, Role
from src.app.polygon.repository import (
    PolygonConfigMySQLRepo,
    PolygonConfigRepo,
    PolygonObjectMySQLRepo,
    PolygonObjectRepo,
)
from src.app.role.repository import (
    BaseRoleMySQLRepo,
    BaseRoleRepo,
    RoleMySQLRepo,
    RoleRepo,
)
from src.app.role.unit_of_work import RoleUnitOfWork
from src.core.database import DbSessionDep, DbSessionDepReadOnly
from src.core.unit_of_work import UnitOfWorkBase
from src.core.utils import datetime_now


class PolygonUnitOfWork(UnitOfWorkBase):
    polygon_config_repo: PolygonConfigRepo
    polygon_object_repo: PolygonObjectRepo
    role_repo: RoleRepo
    base_role_repo: BaseRoleRepo

    def __init__(self, session: AsyncSession):
        self.db_session = session

        self.polygon_config_repo = PolygonConfigMySQLRepo(session)
        self.polygon_object_repo = PolygonObjectMySQLRepo(session)
        self.role_repo = RoleMySQLRepo(session)
        self.base_role_repo = BaseRoleMySQLRepo(session)

    async def create_polygon_config(
        self, config_schema: CreatePolygonConfigRequest, role_uow: RoleUnitOfWork
    ) -> PolygonConfig:
        polygon_config_db = PolygonConfig(
            name=config_schema.name,
            description=config_schema.description,
            arena_width=config_schema.arena_width,
            created_at=datetime_now(),
        )
        polygon_objects_db: list[PolygonObject] = []
        for polygon_obj in config_schema.polygon_manager:
            polygon_objects_db.append(
                PolygonObject(
                    id_on_map=polygon_obj.id_on_map
                    if polygon_obj.id_on_map is not None
                    else config_schema.polygon_manager.index(polygon_obj),
                    color=polygon_obj.vis_info.color,
                    position=polygon_obj.position,
                    description=polygon_obj.vis_info.description,
                    ind_for_led_controller=polygon_obj.ind_for_led_controller
                    if polygon_obj.ind_for_led_controller is not None
                    and polygon_obj.ind_for_led_controller >= 0
                    else None,
                    scale=polygon_obj.scale,
                    role=await role_uow.create_missing_role(
                        polygon_obj.role, polygon_obj.custom_settings
                    ),
                )
            )

        polygon_config_db.polygon_objects = polygon_objects_db

        await self.polygon_object_repo.add_many_orm(polygon_objects_db, flushing=False)
        await self.polygon_config_repo.add(polygon_config_db, flushing=False)

        # await self.db_session.flush()

        return polygon_config_db

    async def generate_polygon_config_by_polygon_manager(
        self, config_schema: CreatePolygonConfigRequest, role_uow: RoleUnitOfWork
    ) -> PolygonConfig:
        last_insert_id = await self.polygon_config_repo.get_last_id()
        if last_insert_id:
            config_schema.name = f"via json {last_insert_id + 1}"
        config_db = await self.polygon_config_repo.get_by_name_with_objects(
            config_schema.name
        )
        if not config_db:
            config_db = await self.create_polygon_config(config_schema, role_uow)
        return config_db

    async def edit_polygon_config(
        self,
        config,
        edit_polygon_config_data: ReplacePolygonConfigWithObjectsRequest,
    ) -> bool:
        if isinstance(config, int):
            config_db: PolygonConfig = (
                await self.polygon_config_repo.get_by_id_with_objects(config)
            )
        elif isinstance(config, PolygonConfig):
            config_db: PolygonConfig = config
        else:
            return False

        if edit_polygon_config_data.name is not None:
            config_db.name = edit_polygon_config_data.name

        if edit_polygon_config_data.arena_width is not None:
            config_db.arena_width = edit_polygon_config_data.arena_width

        if edit_polygon_config_data.created_at is not None:
            if isinstance(edit_polygon_config_data.created_at, datetime):
                config_db.created_at = edit_polygon_config_data.created_at
            elif isinstance(edit_polygon_config_data.created_at, str):
                config_db.created_at = datetime.fromisoformat(
                    edit_polygon_config_data.created_at
                )

        if edit_polygon_config_data.description is not None:
            config_db.description = edit_polygon_config_data.description

        if edit_polygon_config_data.polygon_manager:
            old_polygon_obj_by_id_on_map = {
                obj.id_on_map: obj for obj in config_db.polygon_objects
            }
            new_ids_on_map = set(
                map(lambda obj: obj.id_on_map, edit_polygon_config_data.polygon_manager)
            )
            old_ids_on_map = set(
                map(lambda obj: obj.id_on_map, config_db.polygon_objects)
            )

            if new_ids_on_map.issubset(old_ids_on_map):
                diff_ids_on_map = old_ids_on_map.difference(new_ids_on_map)
                if len(diff_ids_on_map) != 0:
                    for id_on_map in diff_ids_on_map:
                        deleting_obj = old_polygon_obj_by_id_on_map.get(id_on_map, None)
                        if deleting_obj is not None:
                            await self.db_session.delete(deleting_obj)

            for edited_polygon_object in edit_polygon_config_data.polygon_manager:
                old_polygon_object_db: PolygonObject = old_polygon_obj_by_id_on_map.get(
                    edited_polygon_object.id_on_map, None
                )

                if (
                    old_polygon_object_db is None
                ):  # если в запросе появился новый объект
                    new_polygon_object = PolygonObject(polygon_config=config_db)

                    new_polygon_object.position = edited_polygon_object.position
                    new_polygon_object.color = edited_polygon_object.vis_info.color
                    new_polygon_object.description = edited_polygon_object.vis_info.description
                    new_polygon_object.ind_for_led_controller = (
                        edited_polygon_object.ind_for_led_controller
                    )
                    new_polygon_object.scale = edited_polygon_object.scale
                    new_polygon_object.id_on_map = edited_polygon_object.id_on_map
                    new_polygon_object.role_id = edited_polygon_object.role_id

                    await self.polygon_object_repo.add(entity=new_polygon_object)
                    old_polygon_obj_by_id_on_map[edited_polygon_object.id_on_map] = (
                        new_polygon_object
                    )
                    continue

                if edited_polygon_object.position is not None:
                    old_polygon_object_db.position = edited_polygon_object.position

                old_polygon_object_db.ind_for_led_controller = (
                    edited_polygon_object.ind_for_led_controller
                )

                if edited_polygon_object.scale is not None:
                    old_polygon_object_db.scale = edited_polygon_object.scale

                if edited_polygon_object.vis_info.color is not None:
                    old_polygon_object_db.color = edited_polygon_object.vis_info.color

                if edited_polygon_object.vis_info.description is not None:
                    old_polygon_object_db.description = (
                        edited_polygon_object.vis_info.description
                    )

                if edited_polygon_object.role_id is not None:
                    new_custom_role_db: Role = await self.role_repo[
                        edited_polygon_object.role_id
                    ]
                    if (
                        new_custom_role_db.base_role_id
                        != old_polygon_object_db.role.base_role_id
                    ):
                        raise HTTPException(
                            400, detail="Невозможно изменить базовую роль на объекте"
                        )
                    old_polygon_object_db.role_id = new_custom_role_db.id

        return True


def polygon_unit_of_work_maker(is_readonly: bool = False):
    def readonly(db_session: DbSessionDepReadOnly):
        return PolygonUnitOfWork(db_session)

    def readwrite(db_session: DbSessionDep):
        return PolygonUnitOfWork(db_session)

    return readonly if is_readonly else readwrite


_polygon_uow_rw = polygon_unit_of_work_maker()
PolygonUnitOfWorkDep = Annotated[PolygonUnitOfWork, Depends(_polygon_uow_rw)]

_polygon_uow_ro = polygon_unit_of_work_maker(is_readonly=True)
ReadOnlyPolygonUnitOfWorkDep = Annotated[PolygonUnitOfWork, Depends(_polygon_uow_ro)]

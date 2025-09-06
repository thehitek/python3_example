from fastapi import APIRouter, Depends, status

from src.app.auth.service import CheckRole
from src.app.polygon.service import PolygonServiceDep
from src.app.polygon.unit_of_work import (
    PolygonUnitOfWorkDep,
    ReadOnlyPolygonUnitOfWorkDep,
)
from src.app.role.models import UserRoleEnum
from src.app.role.unit_of_work import RoleUnitOfWorkDep
from src.core.exceptions.db import not_found_entity_exc
from src.core.responses import NotReadResponse

from .request import CreatePolygonConfigRequest, ReplacePolygonConfigWithObjectsRequest
from .response import GetPolygonConfigSchema, GetPolygonConfigWithObjectsResponse

polygons_router_v1 = APIRouter(prefix="/v1/polygons", tags=["Polygons | v1"])

polygons_router_v2 = APIRouter(prefix="/v2/polygons", tags=["Polygons | v2"])

@polygons_router_v1.delete(
    "/config",
    response_model=NotReadResponse,
    dependencies=[Depends(CheckRole([UserRoleEnum.AdminRole]))],
    description="""
Удалить карту полигона по имени.\n
Также удалятся все объекты, принадлежащие ей.
""",
)
async def delete_polygon_config_by_name(
    *, name: str, polygon_service: PolygonServiceDep, polygon_uow: PolygonUnitOfWorkDep
):
    # async with polygon_uow.begin() as uow:
    config_db = await polygon_service.get_polygon_config_by_name(name, polygon_uow)
    if config_db is not None:
        await polygon_uow.polygon_config_repo.delete(config_db)
    else:
        raise not_found_entity_exc

    return NotReadResponse(status=200, detail="Deleted by name")


@polygons_router_v1.delete(
    "/config/{id}",
    response_model=NotReadResponse,
    dependencies=[Depends(CheckRole([UserRoleEnum.AdminRole]))],
    description="""
Удалить карту полигона по id в БД.\n
Также удалятся все объекты, принадлежащие ей.
""",
)
async def delete_polygon_config_by_id(*, id: int, polygon_uow: PolygonUnitOfWorkDep):
    # async with polygon_uow.begin() as uow:
    config_db = await polygon_uow.polygon_config_repo.get_by_id(id)
    if config_db is not None:
        await polygon_uow.polygon_config_repo.delete(config_db)
    else:
        raise not_found_entity_exc

    return NotReadResponse(status=200, detail="Deleted by id")


# END VERSION 1 #

# v2 #


@polygons_router_v2.post(
    "/config",
    response_model=GetPolygonConfigSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(CheckRole([UserRoleEnum.AdminRole]))],
    description="""
Создать карту по определенной схеме.\n
Есть возможность создать только по Polygon_manager, который валиден для игрового сервера, оставив остальные поля пустыми.
""",
)
async def create_config(
    *,
    config_data: CreatePolygonConfigRequest,
    polygon_uow: PolygonUnitOfWorkDep,
    role_uow: RoleUnitOfWorkDep,
):
    polygon_config_db = await polygon_uow.create_polygon_config(config_data, role_uow)
    await role_uow.db_session.flush([polygon_config_db])
    return GetPolygonConfigSchema.model_validate(
        polygon_config_db, from_attributes=True, strict=False
    )


@polygons_router_v2.get(
    "/config",
    dependencies=[Depends(CheckRole([UserRoleEnum.AdminRole]))],
    description="""
Получить описания карт без объектов.\n
Можно отфильтровать параметрами запросов.
""",
)
async def get_configs(
    *,
    name: str = None,
    polygon_uow: ReadOnlyPolygonUnitOfWorkDep,
    polygon_service: PolygonServiceDep,
):
    configs_db = await polygon_service.get_configs_with_parameters(name, polygon_uow)
    return configs_db


@polygons_router_v2.put(
    "/config/{id}",
    response_model=NotReadResponse,
    dependencies=[Depends(CheckRole([UserRoleEnum.AdminRole]))],
    description="""
""",
)
async def edit_config_by_id(
    *,
    id: int,
    edit_polygon_config_data: ReplacePolygonConfigWithObjectsRequest,
    polygon_uow: PolygonUnitOfWorkDep,
):
    config_db = await polygon_uow.polygon_config_repo.get_by_id_with_objects(id)
    if config_db is None:
        raise not_found_entity_exc

    edit_config_res = await polygon_uow.edit_polygon_config(
        config_db, edit_polygon_config_data
    )

    if edit_config_res:
        return NotReadResponse(
            status=200,
            detail=f"Данные о карте успешно изменены. id: {config_db.id}; name: {config_db.name}",
        )
    else:
        return NotReadResponse(
            status=500,
            detail=f"Произошла ошибка при попытке изменения данных. id: {config_db.id}; name: {config_db.name}",
        )


@polygons_router_v2.get(
    "/config/{id}",
    response_model=GetPolygonConfigWithObjectsResponse,
    dependencies=[Depends(CheckRole([UserRoleEnum.AdminRole]))],
    description="""
Получить игровую карту по id в базе данных.
""",
)
async def get_config_by_id(
    *,
    id: int,
    polygon_service: PolygonServiceDep,
    polygon_uow: ReadOnlyPolygonUnitOfWorkDep,
):
    config_db = await polygon_uow.polygon_config_repo.get_by_id_with_objects(id)
    if config_db is None:
        raise not_found_entity_exc
    polygon_objects = polygon_service.get_config_with_objects(config_db)

    return GetPolygonConfigWithObjectsResponse(
        id=config_db.id,
        name=config_db.name,
        description=config_db.description,
        arena_width=config_db.arena_width,
        created_at=config_db.created_at,
        polygon_objects=polygon_objects,
    )


# v2 #

# MAIN POLYGON ROUTER #
polygons_router = APIRouter()
polygons_router.include_router(polygons_router_v1)
polygons_router.include_router(polygons_router_v2)

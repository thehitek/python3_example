from typing import Annotated

from fastapi import Depends

from src.api.polygon.response import GetPolygonConfigSchema, GetPolygonObjectResponse
from src.app.all_models import PolygonConfig, PolygonObject
from src.app.game.schemas import GameJsonSchema
from src.app.polygon.unit_of_work import PolygonUnitOfWork


class PolygonService:
    async def get_polygon_config(
        self, input_config: list[PolygonObject], polygon_uow: PolygonUnitOfWork
    ) -> PolygonConfig | None:
        configs_db = await polygon_uow.polygon_config_repo.get_all_with_objects()
        for config_item in configs_db:
            if set(input_config) == set(config_item.polygon_objects):
                return await polygon_uow.polygon_config_repo.get_by_id(config_item.id)

    def get_config_with_objects(
        self, config_db: PolygonConfig
    ) -> list[GetPolygonObjectResponse]:
        polygon_objects: list[PolygonObject] = sorted(
            config_db.polygon_objects, key=lambda poly: poly.id
        )
        polygons_json: list[GetPolygonObjectResponse] = []
        for polygon_obj in polygon_objects:
            polygons_json.append(
                GetPolygonObjectResponse(
                    id_on_map=polygon_obj.id_on_map,
                    custom_settings=polygon_obj.role.custom_settings,
                    ind_for_led_controller=polygon_obj.ind_for_led_controller
                    if polygon_obj.ind_for_led_controller is not None
                    and polygon_obj.ind_for_led_controller >= 0
                    else None,
                    position=polygon_obj.position,
                    scale=polygon_obj.scale,
                    role=polygon_obj.role.base_role.name,
                    role_id=polygon_obj.role_id,
                    base_role_id=polygon_obj.role.base_role.id,
                    vis_info=GameJsonSchema.PolygonObject.VisInfo(
                        color=polygon_obj.color, description=polygon_obj.description
                    ),
                )
            )
        return polygons_json

    async def get_all_configs(
        self, polygon_uow: PolygonUnitOfWork
    ) -> list[GetPolygonConfigSchema]:
        all_configs_db = await polygon_uow.polygon_config_repo.get_all()
        return [
            GetPolygonConfigSchema.model_validate(config, from_attributes=True)
            for config in all_configs_db
        ]

    async def get_polygon_config_by_name(
        self, name: str, polygon_uow: PolygonUnitOfWork
    ) -> PolygonConfig | None:
        return await polygon_uow.polygon_config_repo.get_by_name(name)

    async def get_configs_with_parameters(
        self, name: str | None, polygon_uow: PolygonUnitOfWork
    ) -> list[PolygonConfig]:
        values = [(PolygonConfig.name == name) if name else None]
        result = await polygon_uow.polygon_config_repo.get_all_with_parameters(
            *[value for value in values if value is not None]
        )
        return result


PolygonServiceDep = Annotated[PolygonService, Depends(lambda: PolygonService())]

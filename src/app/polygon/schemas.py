from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class PolygonSchema(BaseModel):
    color: Annotated[list[int], Field(min_items=3, max_items=3)]
    ind_for_led_controller: int | None = None
    position: list
    description: str
    role_id: int
    polygon_config_id: int
    custom_settings: dict = {}
    model_config = ConfigDict(from_attributes=True)


class EditPolygonSchema(BaseModel):
    color: list[int] | None = None
    ind_for_led_controller: int | None = None
    position: list | None = None
    description: str | None = None
    role_id: int | None = None
    model_config = ConfigDict(from_attributes=True)


class PolygonConfigDescriptionSchema(BaseModel):
    name: str | None
    description: str | None
    arena_width: float | None
    created_at: datetime | str


# class PolygonConfigDescriptionNoneDefaultSchema(PolygonConfigDescriptionSchema):
#     name: str | None = None
#     description: str | None = None
#     arena_width: float | None = None
#     created_at: datetime | str | None = None

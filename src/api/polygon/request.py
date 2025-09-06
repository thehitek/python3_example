from datetime import datetime
from pydantic import BaseModel
from src.app.game.schemas import GameJsonSchema
from src.app.polygon.schemas import (
    # PolygonConfigDescriptionNoneDefaultSchema,
    EditPolygonSchema,
)


class PolygonForWebRequest(GameJsonSchema.PolygonObject):
    id_on_map: int | None = None
    scale: float | None = None
    role_id: int | None = None
    base_role_id: int | None = None


# class EditPolygonForWebRequest(EditPolygonSchema):
#     id_on_map: int
#     scale: float | None = 1.0


class CreatePolygonConfigRequest(BaseModel):
    name: str = ""
    description: str | None = ""
    arena_width: float | int | None = 0.0
    polygon_manager: list[PolygonForWebRequest]


# class ReplacePolygonConfigWithObjectsRequest(PolygonConfigDescriptionNoneDefaultSchema):
#     polygon_manager: list[EditPolygonForWebRequest] | None = None

class ReplacePolygonConfigWithObjectsRequest(CreatePolygonConfigRequest):
    created_at: datetime | str | None = None
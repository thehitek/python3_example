from pydantic import ConfigDict

from src.app.polygon.schemas import PolygonConfigDescriptionSchema

from .request import PolygonForWebRequest


class GetPolygonConfigSchema(PolygonConfigDescriptionSchema):
    id: int
    model_config = ConfigDict(from_attributes=True)


class GetPolygonObjectResponse(PolygonForWebRequest):
    id_on_map: int
    scale: float


class GetPolygonConfigWithObjectsResponse(GetPolygonConfigSchema):
    polygon_objects: list[GetPolygonObjectResponse]

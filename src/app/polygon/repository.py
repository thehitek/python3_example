from abc import ABCMeta, abstractmethod

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import joinedload
from src.app.all_models import Role
from src.app.polygon.models import PolygonConfig, PolygonObject
from src.core.repository import RepositoryABCBase, RepositoryMySQLBase


class PolygonObjectRepo(RepositoryABCBase, metaclass=ABCMeta):
    pass
    @abstractmethod
    async def get_all_by_polygon_config_id(self, polygon_config_id: int) -> list[PolygonObject]:
        pass


class PolygonObjectMySQLRepo(PolygonObjectRepo, RepositoryMySQLBase):
    base_entity = PolygonObject

    async def get_all_by_polygon_config_id(self, polygon_config_id: int):
        result = await self.session.scalars(
            select(PolygonObject).where(PolygonObject.polygon_config_id == polygon_config_id)
        )
        return result.all()


class PolygonConfigRepo(RepositoryABCBase, metaclass=ABCMeta):
    @abstractmethod
    async def get_all_with_objects(self) -> list[PolygonConfig]:
        pass

    @abstractmethod
    async def get_by_id_with_objects(self, id: int) -> PolygonConfig | None:
        pass

    @abstractmethod
    async def get_by_id(self, id: int) -> PolygonConfig | None:
        pass

    @abstractmethod
    async def get_all(self) -> list[PolygonConfig]:
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> PolygonConfig | None:
        pass

    @abstractmethod
    async def get_by_name_with_objects(self, name: str) -> PolygonConfig | None:
        pass

    @abstractmethod
    async def get_all_with_parameters(self, *args) -> list[PolygonConfig]:
        pass

    @abstractmethod
    async def get_last_id(self) -> int | None:
        pass

    @abstractmethod
    async def delete(self, polygon_config_db: PolygonConfig):
        pass



class PolygonConfigMySQLRepo(PolygonConfigRepo, RepositoryMySQLBase):
    base_entity = PolygonConfig

    async def get_all_with_objects(self) -> list[PolygonConfig]:
        result = await self.session.scalars(
            select(PolygonConfig).options(joinedload(PolygonConfig.polygon_objects))
        )
        return result.unique().all()

    async def get_by_id_with_objects(self, id: int) -> PolygonConfig | None:
        result = await self.session.scalar(
            select(PolygonConfig)
            .where(PolygonConfig.id == id)
            .options(
                joinedload(PolygonConfig.polygon_objects)
                .joinedload(PolygonObject.role)
                .joinedload(Role.base_role)
            )
        )
        return result

    async def get_by_id(self, id: int) -> PolygonConfig | None:
        result = await self.session.get(PolygonConfig, id)
        return result

    async def get_all(self) -> list[PolygonConfig]:
        result = await self.session.scalars(select(PolygonConfig))
        return result.all()

    async def get_by_name(self, name: str) -> PolygonConfig | None:
        result = await self.session.scalar(
            select(PolygonConfig).where(PolygonConfig.name == name)
        )
        return result

    async def get_by_name_with_objects(self, name: str) -> PolygonConfig | None:
        result = await self.session.scalar(
            select(PolygonConfig)
            .where(PolygonConfig.name == name)
            .options(joinedload(PolygonConfig.polygon_objects))
        )
        return result

    async def get_all_with_parameters(self, *args) -> list[PolygonConfig]:
        result = await self.session.scalars(
            select(PolygonConfig).where(and_(True, *args))
        )
        return result.all()

    async def get_last_id(self) -> int | None:
        result = await self.session.scalar(
            select(PolygonConfig.id).order_by(desc(PolygonConfig.id)).limit(1)
        )
        return result

    async def delete(self, polygon_config_db: PolygonConfig):
        await self.session.delete(polygon_config_db)

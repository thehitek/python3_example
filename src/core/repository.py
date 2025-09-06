from abc import ABCMeta, abstractmethod
from typing import Iterable
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from . import custom_logging
from src.core.database import Base


class RepositoryABCBase(metaclass=ABCMeta):
    @abstractmethod
    async def add(self, entity: Base, flushing: bool = True):
        pass

    @abstractmethod
    async def add_many_orm(self, entities: Iterable[Base], flushing: bool = True):
        pass

    @abstractmethod
    async def set_attr(self, attr: str, value, where_args):
        pass

class RepositoryMySQLBase(RepositoryABCBase):
    base_entity = None

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    def __getitem__(self, id: int):
        if not isinstance(id, int):
            raise TypeError("Id must be integer")
        return None if not self.base_entity else self.session.get(self.base_entity, id)

    async def add(self, entity: Base, flushing: bool = True):
        self.session.add(entity)
        if flushing:
            await self.session.flush([entity])

    async def add_many_orm(self, entities: Iterable[Base], flushing: bool = True):
        self.session.add_all(entities)
        if flushing:
            await self.session.flush(entities)

    async def set_attr(self, attr, value, where_args):
        '''UPDATE {base_entity} WHERE {where_args} SET VALUE {value}
        '''
        if not hasattr(self.base_entity, attr):
            custom_logging.error(f"[set_attr_entities] Invalid args")
            return False
            
        stmt = update(self.base_entity).values({attr: value})
        if where_args: stmt.where(*where_args)
        
        res = await self.session.execute(stmt)
        return res.rowcount
        
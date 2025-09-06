from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWorkBase:
    db_session: AsyncSession

    @asynccontextmanager
    async def begin_nested(self):
        nested = self.db_session.begin_nested()
        await nested.start()
        try:
            yield self
        except Exception as exc:
            raise exc
        finally:
            await nested.commit()

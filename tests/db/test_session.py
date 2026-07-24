import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db.session import create_engine, get_db_session


def test_create_engine_targets_configured_database_url() -> None:
    engine = create_engine()
    assert isinstance(engine, AsyncEngine)
    assert engine.url.drivername == "postgresql+asyncpg"


async def test_get_db_session_yields_a_closable_async_session() -> None:
    session_gen = get_db_session()
    session = await anext(session_gen)
    try:
        assert isinstance(session, AsyncSession)
    finally:
        await session.close()
        with pytest.raises(StopAsyncIteration):
            await anext(session_gen)

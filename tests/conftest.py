from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

_settings = get_settings()
TEST_DATABASE_URL = _settings.database_url.rsplit("/", 1)[0] + "/dataflow_test"


async def _ensure_test_database_exists() -> None:
    # asyncpg can't run CREATE DATABASE inside a transaction, so this connection
    # needs autocommit isolation rather than the default transactional one.
    admin_engine = create_async_engine(_settings.database_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = 'dataflow_test'")
        )
        if not exists:
            await conn.execute(text("CREATE DATABASE dataflow_test"))
    await admin_engine.dispose()


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    # Function-scoped (not session-scoped): asyncpg connections are bound to the event
    # loop they were created on, and pytest-asyncio gives each test function its own
    # loop. A shared engine would hand out connections tied to a stale loop and fail
    # with "attached to a different loop". Recreating per test costs a bit of setup
    # time but keeps every test on a single, consistent event loop.
    await _ensure_test_database_exists()
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

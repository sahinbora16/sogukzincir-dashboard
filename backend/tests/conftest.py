import os
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

import database  # imported so we can patch its module-level globals

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://sogukzincir:sogukzincir@localhost:5432/sogukzincir_test",
)

_test_engine = create_async_engine(TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(_test_engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Redirect every SQLAlchemy session (request scope AND background tasks)
    to the test database for the whole session.
    """
    from database import Base

    database.engine = _test_engine
    database.AsyncSessionLocal = _TestSessionLocal

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _test_engine.dispose()


@pytest.fixture(autouse=True)
async def clean_tables():
    """Truncate all tables between tests for isolation."""
    yield
    async with _TestSessionLocal() as db:
        from sqlalchemy import text
        await db.execute(text("TRUNCATE logistics_fleet, alerts RESTART IDENTITY CASCADE"))
        await db.commit()


@pytest.fixture
async def db():
    async with _TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    from main import app
    from database import get_db

    async def _override_get_db():
        async with _TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_vehicle(db):
    from models import LogisticsFleet

    v = LogisticsFleet(
        vehicle_id="TEST-001",
        driver_name="Test Sürücü",
        status="idle",
        current_lat=40.1833,
        current_lng=28.1333,
        speed=0.0,
        temperature=4.0,
        load_level=0.0,
        capacity=5000.0,
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return v

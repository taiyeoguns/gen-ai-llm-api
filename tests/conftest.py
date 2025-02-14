from collections.abc import Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app import create_app
from app.common.database import Base


@pytest.fixture
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("timescale/timescaledb-ha:pg17") as postgres:
        yield postgres


@pytest.fixture(name="test_engine")
def fixture_test_engine(postgres_container: PostgresContainer):
    async_db_url = postgres_container.get_connection_url().replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://"
    )
    yield create_async_engine(async_db_url)


@pytest.fixture(name="application")
def fixture_application():
    """Fixture to set up application with configuration

    Returns:
        application -- Application context
    """
    yield create_app()


@pytest_asyncio.fixture(name="setup_db")
async def fixture_setup_db(test_engine):
    async def inner():
        async with test_engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS ai CASCADE;"))
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    return inner


@pytest.fixture(name="client")
def fixture_client(application):
    """Fixture for HTTP test client

    Arguments:
        application -- Application context

    Returns:
        client -- HTTP client
    """
    return TestClient(application)


@pytest_asyncio.fixture(name="test_session")
async def fixture_test_session(test_engine, setup_db):
    SessionLocal = async_sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    async with SessionLocal() as session:
        await setup_db()
        yield session


@pytest_asyncio.fixture(name="get_test_session")
async def fixture_get_test_session(test_session):
    async def inner():
        return test_session

    return inner

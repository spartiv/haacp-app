from collections.abc import AsyncGenerator, Generator

import boto3
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from moto import mock_aws
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app as fastapi_app
from app.models import *  # noqa: F401,F403  registers all models on Base.metadata
from app.models.allergen import LEGAL_ALLERGENS, Allergen
from app.models.event_log_type import EVENT_LOG_TYPES, EventLogType
from app.services.email_sender import get_email_sender
from app.services.storage import S3StorageBackend, get_storage_backend
from tests.fakes import FakeEmailSender


@pytest.fixture(scope="session")
def postgres_container() -> AsyncGenerator[PostgresContainer]:
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as container:
        yield container


@pytest_asyncio.fixture(scope="session")
async def engine(postgres_container: PostgresContainer) -> AsyncGenerator[AsyncEngine]:
    test_engine = create_async_engine(postgres_container.get_connection_url())
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    # create_all builds tables but skips migration data seeds (e.g. the
    # legal allergen list), so mirror that seed here.
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add_all(
            [
                Allergen(name=name, position=position)
                for position, name in enumerate(LEGAL_ALLERGENS)
            ]
        )
        session.add_all(
            [
                EventLogType(position=position, **entry)
                for position, entry in enumerate(EVENT_LOG_TYPES)
            ]
        )
        await session.commit()

    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """Each test runs inside a transaction that's rolled back afterwards, for isolation."""
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        async with session_factory() as session:
            yield session
        await transaction.rollback()


@pytest.fixture
def fake_email_sender() -> FakeEmailSender:
    return FakeEmailSender()


@pytest.fixture
def s3_storage() -> Generator[S3StorageBackend]:
    """S3-backed storage for service-level tests that call attachment_service
    (or its callers) directly, without going through the HTTP `client`
    fixture. moto mocks the AWS calls against an in-memory fake."""
    settings = get_settings()
    with mock_aws():
        boto3.client("s3", region_name=settings.aws_region).create_bucket(
            Bucket=settings.s3_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
        )
        yield S3StorageBackend(bucket_name=settings.s3_bucket_name, region=settings.aws_region)


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession, fake_email_sender: FakeEmailSender
) -> AsyncGenerator[AsyncClient]:
    """HTTP client for router tests; the app's DB, email, and file-storage
    dependencies are overridden so requests share the same per-test
    transaction as `db_session` (rolled back with it), never touch real
    email, and never touch a real S3 bucket (moto mocks AWS calls against
    an in-memory fake for the duration of the test)."""

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession]:
        yield db_session

    settings = get_settings()
    with mock_aws():
        boto3.client("s3", region_name=settings.aws_region).create_bucket(
            Bucket=settings.s3_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
        )
        test_storage = S3StorageBackend(
            bucket_name=settings.s3_bucket_name, region=settings.aws_region
        )
        fastapi_app.dependency_overrides[get_db_session] = _override_get_db_session
        fastapi_app.dependency_overrides[get_email_sender] = lambda: fake_email_sender
        fastapi_app.dependency_overrides[get_storage_backend] = lambda: test_storage
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
        fastapi_app.dependency_overrides.pop(get_db_session, None)
        fastapi_app.dependency_overrides.pop(get_email_sender, None)
        fastapi_app.dependency_overrides.pop(get_storage_backend, None)

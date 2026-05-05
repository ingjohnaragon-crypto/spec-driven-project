import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from main import app
from src.infrastructure.database.engine import Base, get_async_session

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, future=True, echo=False)
AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def initialized_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def session(initialized_db) -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session


@pytest.fixture(autouse=True)
def override_dependencies(session: AsyncSession):
    async def get_test_session() -> AsyncSession:
        async with AsyncSessionFactory() as test_session:
            yield test_session

    app.dependency_overrides[get_async_session] = get_test_session
    yield
    app.dependency_overrides.clear()

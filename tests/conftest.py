import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, DATABASE_URL

# 1. REMOVED: global test_engine = ...
#    (We don't want the engine created at import time)

# 2. REMOVED: event_loop fixture
#    (Let pytest-asyncio handle the loop automatically)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates a fresh database session for a single test.
    """
    # A. Create the Engine INSIDE the test's event loop
    engine = create_async_engine(DATABASE_URL, echo=False)

    # B. Create the Session Factory
    session_factory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # C. Setup the Database (Create Tables)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Safety clean
        await conn.run_sync(Base.metadata.create_all)

    # D. Yield the Session to the test
    async with session_factory() as session:
        yield session
        await session.rollback()

    # E. Cleanup (Drop Tables & Close Engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

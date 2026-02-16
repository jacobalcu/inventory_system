import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Get URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create Async Engine
# echo=True means print every SQL query to the console
# Crucial for debugging, but should be turned off in production
engine = create_async_engine(DATABASE_URL, echo=True)

# Create Session factory
# Use to create new sessions for every request
# expire_on_commit=False prevents generic "Session is closed" errors after we commit
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Declarative Base
# All models inherit from this class
Base = declarative_base()


# Dependency Injection
# Helper func used in FastAPI endpoints later
# Ensures we open a session, use it, and CLOSE it even if there's an error
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

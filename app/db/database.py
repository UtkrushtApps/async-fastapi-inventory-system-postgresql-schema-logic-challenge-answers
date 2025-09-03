from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/inventory_db")

async_engine: AsyncEngine = create_async_engine(DATABASE_URL, future=True, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

def get_async_session():
    # This function is yield-based for dependency injection
    async def _get_session() -> AsyncSession:
        async with AsyncSessionLocal() as session:
            yield session
    return _get_session

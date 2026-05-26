from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from auth.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
	pass


engine = create_async_engine(
	url=settings.DATABASE_URL,
	echo=settings.DEBUG,
	pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
	bind=engine, class_=AsyncSession, autoflush=False, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:  # pragma: no cover
	async with AsyncSessionLocal() as session:
		try:
			yield session
		except Exception:
			await session.rollback()
			raise

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from auth.config import get_settings
from auth.database_url import normalize_async_database_url

settings = get_settings()


class Base(DeclarativeBase):
	pass


database_url, connect_args = normalize_async_database_url(settings.DATABASE_URL)

engine = create_async_engine(
	url=database_url,
	echo=settings.DEBUG,
	pool_pre_ping=True,
	connect_args=connect_args,
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

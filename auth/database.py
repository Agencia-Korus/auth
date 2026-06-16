from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from auth.config import get_settings

settings = get_settings()

NOMES_DRIVERS_POSTGRES = {'postgres', 'postgresql', 'postgresql+asyncpg'}


def normalizar_url_banco_assincrono(url: str) -> tuple[str, dict[str, Any]]:
	"""Normaliza a URL para asyncpg, repassando o DSN cru (suporta sslmode do Neon)."""
	url_analisada = make_url(url)
	if url_analisada.drivername not in NOMES_DRIVERS_POSTGRES:
		return str(url_analisada), {}

	dsn_asyncpg = url_analisada.set(drivername='postgresql')
	return 'postgresql+asyncpg://', {'dsn': dsn_asyncpg.render_as_string(hide_password=False)}


class Base(DeclarativeBase):
	pass


_url_banco, _argumentos_conexao = normalizar_url_banco_assincrono(settings.DATABASE_URL)

engine = create_async_engine(
	url=_url_banco,
	echo=settings.DEBUG,
	pool_pre_ping=True,
	connect_args=_argumentos_conexao,
)

AsyncSessionLocal = async_sessionmaker(
	bind=engine, class_=AsyncSession, autoflush=False, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:  # pragma: no cover
	"""Fornece uma sessão assíncrona por requisição."""
	async with AsyncSessionLocal() as session:
		try:
			yield session
		except Exception:
			await session.rollback()
			raise

import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
	AsyncEngine,
	AsyncSession,
	async_sessionmaker,
	create_async_engine,
)
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from auth.app import app
from auth.database import Base, get_session

BASE_URL_ENV = 'KORUS_AUTH_BASE_URL'
DEFAULT_TIMEOUT_SECONDS = 30
POSTGRES_IMAGE = 'postgres:18'

CREATE_USER_ROLE_TYPE = """
DO $$
BEGIN
	CREATE TYPE user_role AS ENUM ('cliente', 'funcionario', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL;
END
$$;
"""

CREATE_USER_STATUS_TYPE = """
DO $$
BEGIN
	CREATE TYPE user_status AS ENUM ('ativo', 'inativo', 'pendente');
EXCEPTION WHEN duplicate_object THEN NULL;
END
$$;
"""
TRUNCATE_TABLES = 'TRUNCATE TABLE admin, cliente, funcionario, usuario RESTART IDENTITY CASCADE'


@pytest.fixture(scope='session')
def base_url() -> str | None:
	"""Retorna a URL externa da API quando os testes apontam para serviço real."""
	return os.environ.get(BASE_URL_ENV)


@pytest_asyncio.fixture
async def client(base_url: str | None) -> AsyncGenerator[AsyncClient, None]:
	"""Fornece cliente HTTP para API externa ou app ASGI local."""
	if base_url:
		async with AsyncClient(base_url=base_url, timeout=DEFAULT_TIMEOUT_SECONDS) as http_client:
			yield http_client
	else:
		transport = ASGITransport(app=app)
		async with AsyncClient(
			transport=transport,
			base_url='http://testserver',
			timeout=DEFAULT_TIMEOUT_SECONDS,
		) as http_client:
			yield http_client


@pytest.fixture(scope='session')
def postgres_container() -> Generator[PostgresContainer, None, None]:
	"""Sobe um Postgres efêmero para a sessão de testes."""
	with PostgresContainer(POSTGRES_IMAGE, driver='asyncpg') as postgres:
		yield postgres


async def _create_test_schema(engine: AsyncEngine) -> None:
	"""Prepara extensões, enums e tabelas no banco de teste."""
	async with engine.begin() as conn:
		await conn.execute(text('CREATE EXTENSION IF NOT EXISTS citext'))
		await conn.execute(text(CREATE_USER_ROLE_TYPE))
		await conn.execute(text(CREATE_USER_STATUS_TYPE))
		await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture(scope='session', loop_scope='session')
async def db_engine(postgres_container: PostgresContainer) -> AsyncGenerator[AsyncEngine, None]:
	"""Cria engine assíncrono conectado ao Postgres de teste."""
	engine = create_async_engine(
		postgres_container.get_connection_url(),
		poolclass=NullPool,
		pool_pre_ping=True,
	)

	await _create_test_schema(engine)

	try:
		yield engine
	finally:
		await engine.dispose()


@pytest.fixture
def db_sessionmaker(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
	"""Cria factory de sessões para o banco de teste."""
	return async_sessionmaker(
		bind=db_engine,
		class_=AsyncSession,
		autoflush=False,
		expire_on_commit=False,
	)


@pytest_asyncio.fixture
async def db_client(
	db_engine: AsyncEngine,
	db_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
	"""Fornece cliente ASGI com dependência de sessão sobrescrita."""

	async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
		"""Fornece sessões do banco efêmero para as rotas testadas."""
		async with db_sessionmaker() as session:
			try:
				yield session
			except Exception:
				await session.rollback()
				raise

	app.dependency_overrides[get_session] = override_get_session

	transport = ASGITransport(app=app)
	try:
		async with AsyncClient(
			transport=transport,
			base_url='http://testserver',
			timeout=DEFAULT_TIMEOUT_SECONDS,
		) as http_client:
			yield http_client
	finally:
		app.dependency_overrides.pop(get_session, None)

		async with db_engine.begin() as conn:
			await conn.execute(text(TRUNCATE_TABLES))

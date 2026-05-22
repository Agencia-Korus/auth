import asyncio
import os
import socket
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault('DATABASE_URL', 'postgresql+asyncpg://korus:korus@localhost:5432/korus_test')
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret')

from sqlalchemy import text  # noqa: E402

from auth.app import app  # noqa: E402
from auth.database import engine  # noqa: E402

BASE_URL_ENV = 'KORUS_AUTH_BASE_URL'
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_DB_PORT = 5432
SOCKET_CHECK_TIMEOUT = 1


@pytest.fixture(scope='session')
def base_url() -> str | None:
	return os.environ.get(BASE_URL_ENV)


@pytest_asyncio.fixture
async def client(base_url: str | None) -> AsyncGenerator[AsyncClient, None]:
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


async def _ping_database() -> bool:
	try:
		async with engine.connect() as conn:
			await conn.execute(text('SELECT 1 FROM usuario LIMIT 1'))
			return True
	except Exception:
		return False
	finally:
		await engine.dispose()


def is_postgres_available() -> bool:
	host = os.environ.get('TEST_DB_HOST', 'localhost')
	port = int(os.environ.get('TEST_DB_PORT', str(DEFAULT_DB_PORT)))
	try:
		with socket.create_connection((host, port), timeout=SOCKET_CHECK_TIMEOUT):
			pass
	except OSError:
		return False
	try:
		return asyncio.run(_ping_database())
	except RuntimeError:
		return False


requires_db = pytest.mark.skipif(
	not is_postgres_available(),
	reason='Postgres com schema aplicado é necessário',
)

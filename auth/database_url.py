from typing import Any

from sqlalchemy.engine import make_url

POSTGRES_DRIVER_NAMES = {'postgres', 'postgresql', 'postgresql+asyncpg'}


def normalize_async_database_url(url: str) -> tuple[str, dict[str, Any]]:
	parsed_url = make_url(url)
	if parsed_url.drivername not in POSTGRES_DRIVER_NAMES:
		return str(parsed_url), {}

	asyncpg_dsn = parsed_url.set(drivername='postgresql')

	return 'postgresql+asyncpg://', {
		'dsn': asyncpg_dsn.render_as_string(hide_password=False)
	}

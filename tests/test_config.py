from auth.config import Settings
from auth.database_url import normalize_async_database_url


def test_debug_release_is_false():
	settings = Settings(DEBUG='release')

	assert settings.DEBUG is False


def test_normalize_postgresql_url_to_asyncpg_dsn():
	url = 'postgresql://user:pass@example.com:5432/dbname?sslmode=require&channel_binding=require'

	database_url, connect_args = normalize_async_database_url(url)

	assert database_url == 'postgresql+asyncpg://'
	assert connect_args['dsn'].startswith('postgresql://user:pass@example.com:5432/dbname?')
	assert 'sslmode=require' in connect_args['dsn']
	assert 'channel_binding=require' in connect_args['dsn']

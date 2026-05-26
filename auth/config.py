from functools import lru_cache
from typing import Final

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

JWT_DEFAULT_ALGORITHM: Final = 'HS256'
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Final = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS: Final = 7


class Settings(BaseSettings):
	DATABASE_URL: str = 'postgresql+asyncpg://user:pass@host:5432/dbname'
	DEBUG: bool = False
	JWT_SECRET_KEY: str = 'secret-key'
	JWT_ALGORITHM: str = JWT_DEFAULT_ALGORITHM
	JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
	JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = JWT_REFRESH_TOKEN_EXPIRE_DAYS
	CORS_ALLOW_ORIGINS: str = '*'

	@field_validator('DEBUG', mode='before')
	@classmethod
	def parse_debug(cls, value: object) -> object:
		"""Converte aliases de ambiente de produção para DEBUG falso."""
		if isinstance(value, str) and value.strip().lower() in {
			'release',
			'production',
			'prod',
		}:
			return False
		return value

	model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')


@lru_cache
def get_settings() -> Settings:
	"""Retorna configurações cacheadas da aplicação."""
	return Settings()

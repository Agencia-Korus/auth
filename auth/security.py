from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from auth.config import get_settings

_pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
_settings = get_settings()

CREDENTIALS_EXCEPTION = HTTPException(
	status_code=status.HTTP_401_UNAUTHORIZED,
	detail='Credenciais inválidas',
	headers={'WWW-Authenticate': 'Bearer'},
)

TOKEN_TYPE_ACESS = 'access'
TOKEN_TYPE_REFRESH = 'refresh'


def hash_password(plain: str) -> str:
	"""Gera hash seguro para uma senha em texto puro."""
	return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
	"""Verifica se uma senha corresponde ao hash armazenado."""
	return _pwd_context.verify(plain, hashed)


def _create_token(subject: int, token_type: str, expires_delta: timedelta, **extra: Any) -> str:
	"""Cria um JWT assinado com tipo, expiração e dados extras."""
	expire = datetime.now(timezone.utc) + expires_delta
	payload: dict[str, Any] = {'sub': str(subject), 'exp': expire, 'type': token_type, **extra}
	return jwt.encode(payload, _settings.JWT_SECRET_KEY, algorithm=_settings.JWT_ALGORITHM)


def create_access_token(subject: int, role: str) -> str:
	"""Cria token de acesso para um usuário e sua role."""
	return _create_token(
		subject,
		TOKEN_TYPE_ACESS,
		timedelta(minutes=_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
		role=role,
	)


def create_refresh_token(subject: int) -> str:
	"""Cria token de refresh para um usuário."""
	return _create_token(
		subject, TOKEN_TYPE_REFRESH, timedelta(days=_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
	)


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
	"""Decodifica um JWT e valida seu tipo esperado."""
	try:
		payload = jwt.decode(token, _settings.JWT_SECRET_KEY, algorithms=[_settings.JWT_ALGORITHM])
	except JWTError as exc:
		raise CREDENTIALS_EXCEPTION from exc
	if payload.get('type') != expected_type:
		raise CREDENTIALS_EXCEPTION
	return payload

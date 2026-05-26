from http import HTTPStatus

import pytest
from fastapi import HTTPException

from auth.security import (
	TOKEN_TYPE_ACESS,
	TOKEN_TYPE_REFRESH,
	create_access_token,
	create_refresh_token,
	decode_token,
	hash_password,
	verify_password,
)


@pytest.mark.parametrize(
	'senha',
	[
		'simples',
		'com-çedilha',
		'senha-LONGA-12',
	],
)
def test_hash_e_verifica_senha(senha: str):
	"""Garante que senha é hasheada e verificada corretamente."""
	hashed = hash_password(senha)

	assert hashed != senha
	assert verify_password(senha, hashed) is True
	assert verify_password('outra-senha', hashed) is False


@pytest.mark.parametrize(
	('user_id', 'role'),
	[
		(1, 'admin'),
		(5, 'cliente'),
	],
)
def test_access_token_codifica_role(user_id: int, role: str):
	"""Garante que access token carrega usuário, role e tipo."""
	token = create_access_token(user_id, role)

	payload = decode_token(token, TOKEN_TYPE_ACESS)

	assert payload['sub'] == str(user_id)
	assert payload['role'] == role
	assert payload['type'] == TOKEN_TYPE_ACESS


def test_refresh_token_tipo_correto():
	"""Garante que refresh token carrega tipo de refresh."""
	token = create_refresh_token(99)

	payload = decode_token(token, TOKEN_TYPE_REFRESH)

	assert payload['sub'] == '99'
	assert payload['type'] == TOKEN_TYPE_REFRESH


def test_decode_token_rejeita_token_malformado():
	"""Garante que token inválido gera erro de credenciais."""
	with pytest.raises(HTTPException) as exc_info:
		decode_token('token-invalido', TOKEN_TYPE_ACESS)

	assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED


def test_decode_token_rejeita_tipo_incorreto():
	"""Garante que token com tipo inesperado é rejeitado."""
	token = create_refresh_token(99)

	with pytest.raises(HTTPException) as exc_info:
		decode_token(token, TOKEN_TYPE_ACESS)

	assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED

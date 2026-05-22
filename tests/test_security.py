import pytest

from auth.security import (
	TOKEN_TYPE_ACESS,
	TOKEN_TYPE_REFRESH,
	create_access_token,
	create_refresh_token,
	decode_token,
	hash_password,
	verify_password,
)


@pytest.mark.parametrize('senha', ['simples', 'com-çedilha', 'senha-MUITO-longa-123'])
def test_hash_e_verifica_senha(senha: str):
	hashed = hash_password(senha)
	assert verify_password(senha, hashed) is True
	assert verify_password('outra-senha', hashed) is False


@pytest.mark.parametrize(('user_id', 'role'), [(1, 'admin'), (5, 'cliente')])
def test_access_token_codifica_role(user_id: int, role: str):
	token = create_access_token(user_id, role)
	payload = decode_token(token, TOKEN_TYPE_ACESS)
	assert payload['sub'] == str(user_id)
	assert payload['role'] == role


def test_refresh_token_tipo_correto():
	token = create_refresh_token(99)
	payload = decode_token(token, TOKEN_TYPE_REFRESH)
	assert payload['type'] == TOKEN_TYPE_REFRESH

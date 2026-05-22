import uuid
from http import HTTPStatus

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from auth.database import engine
from tests.conftest import requires_db


def _payload():
	suffix = uuid.uuid4().hex[:8]

	return {
		'nome': f'User {suffix}',
		'email': f'user-{suffix}@example.com',
		'senha': 'senha-forte-123',
		'role': 'cliente',
	}


def _login_form(email: str, senha: str):
	return {
		'username': email,
		'password': senha,
	}


@pytest.mark.asyncio
@requires_db
async def test_fluxo_register_login_refresh_me(client: AsyncClient):
	payload = _payload()

	reg = await client.post('/auth/register', json=payload)

	assert reg.status_code == HTTPStatus.CREATED, reg.text
	assert reg.json()['status'] == 'pendente'

	login_pendente = await client.post(
		'/auth/login',
		data=_login_form(payload['email'], payload['senha']),
	)

	assert login_pendente.status_code == HTTPStatus.FORBIDDEN, login_pendente.text

	async with engine.begin() as conn:
		await conn.execute(
			text("UPDATE usuario SET status = 'ativo' WHERE email = :email"),
			{'email': payload['email']},
		)

	login = await client.post(
		'/auth/login',
		data=_login_form(payload['email'], payload['senha']),
	)

	assert login.status_code == HTTPStatus.OK, login.text

	tokens = login.json()

	assert tokens['access_token']
	assert tokens['refresh_token']
	assert tokens['token_type'] == 'Bearer'

	me = await client.get(
		'/auth/me',
		headers={'Authorization': f'Bearer {tokens["access_token"]}'},
	)

	assert me.status_code == HTTPStatus.OK, me.text
	assert me.json()['email'].lower() == payload['email'].lower()

	refreshed = await client.post(
		'/auth/refresh',
		json={'refresh_token': tokens['refresh_token']},
	)

	assert refreshed.status_code == HTTPStatus.OK, refreshed.text
	assert refreshed.json()['access_token']
	assert refreshed.json()['refresh_token']
	assert refreshed.json()['token_type'] == 'Bearer'


@pytest.mark.asyncio
@requires_db
@pytest.mark.parametrize(
	('wrong_senha', 'expected_status'),
	[
		('senha-errada-123', HTTPStatus.UNAUTHORIZED),
		('outra-senha-errada', HTTPStatus.UNAUTHORIZED),
	],
)
async def test_login_invalido(
	client: AsyncClient,
	wrong_senha: str,
	expected_status: HTTPStatus,
):
	payload = _payload()

	reg = await client.post('/auth/register', json=payload)

	assert reg.status_code == HTTPStatus.CREATED, reg.text

	async with engine.begin() as conn:
		await conn.execute(
			text("UPDATE usuario SET status = 'ativo' WHERE email = :email"),
			{'email': payload['email']},
		)

	resp = await client.post(
		'/auth/login',
		data=_login_form(payload['email'], wrong_senha),
	)

	assert resp.status_code == expected_status, resp.text

import uuid
from http import HTTPStatus

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from auth.security import create_access_token, create_refresh_token


def _payload():
	suffix = uuid.uuid4().hex[:8]

	return {
		'nome': f'User {suffix}',
		'email': f'user-{suffix}@example.com',
		'senha': 'senha-forte-123',
		'role': 'cliente',
	}


def _funcionario_payload():
	payload = _payload()
	payload['role'] = 'funcionario'
	payload['funcionario'] = {
		'cargo': 'Designer',
		'especialidade': 'Identidade visual',
	}
	return payload


def _login_form(email: str, senha: str):
	return {
		'username': email,
		'password': senha,
	}


@pytest.mark.asyncio
async def test_fluxo_register_login_refresh_me(
	db_client: AsyncClient,
	db_engine: AsyncEngine,
):
	payload = _payload()

	reg = await db_client.post('/auth/register', json=payload)

	assert reg.status_code == HTTPStatus.CREATED, reg.text
	assert reg.json()['status'] == 'pendente'

	login_pendente = await db_client.post(
		'/auth/login',
		data=_login_form(payload['email'], payload['senha']),
	)

	assert login_pendente.status_code == HTTPStatus.FORBIDDEN, login_pendente.text

	async with db_engine.begin() as conn:
		await conn.execute(
			text("UPDATE usuario SET status = 'ativo' WHERE email = :email"),
			{'email': payload['email']},
		)

	login = await db_client.post(
		'/auth/login',
		data=_login_form(payload['email'], payload['senha']),
	)

	assert login.status_code == HTTPStatus.OK, login.text

	tokens = login.json()

	assert tokens['access_token']
	assert tokens['refresh_token']
	assert tokens['token_type'] == 'Bearer'

	me = await db_client.get(
		'/auth/me',
		headers={'Authorization': f'Bearer {tokens["access_token"]}'},
	)

	assert me.status_code == HTTPStatus.OK, me.text
	assert me.json()['email'].lower() == payload['email'].lower()

	refreshed = await db_client.post(
		'/auth/refresh',
		json={'refresh_token': tokens['refresh_token']},
	)

	assert refreshed.status_code == HTTPStatus.OK, refreshed.text
	assert refreshed.json()['access_token']
	assert refreshed.json()['refresh_token']
	assert refreshed.json()['token_type'] == 'Bearer'


@pytest.mark.asyncio
@pytest.mark.parametrize(
	('wrong_senha', 'expected_status'),
	[
		('senha-errada-123', HTTPStatus.UNAUTHORIZED),
		('outra-senha-errada', HTTPStatus.UNAUTHORIZED),
	],
)
async def test_login_invalido(
	db_client: AsyncClient,
	db_engine: AsyncEngine,
	wrong_senha: str,
	expected_status: HTTPStatus,
):
	payload = _payload()

	reg = await db_client.post('/auth/register', json=payload)

	assert reg.status_code == HTTPStatus.CREATED, reg.text

	async with db_engine.begin() as conn:
		await conn.execute(
			text("UPDATE usuario SET status = 'ativo' WHERE email = :email"),
			{'email': payload['email']},
		)

	resp = await db_client.post(
		'/auth/login',
		data=_login_form(payload['email'], wrong_senha),
	)

	assert resp.status_code == expected_status, resp.text


@pytest.mark.asyncio
async def test_register_rejeita_email_duplicado(db_client: AsyncClient):
	payload = _payload()

	first = await db_client.post('/auth/register', json=payload)
	second = await db_client.post('/auth/register', json=payload)

	assert first.status_code == HTTPStatus.CREATED, first.text
	assert second.status_code == HTTPStatus.CONFLICT, second.text


@pytest.mark.asyncio
async def test_register_rejeita_admin(db_client: AsyncClient):
	payload = _payload()
	payload['role'] = 'admin'

	resp = await db_client.post('/auth/register', json=payload)

	assert resp.status_code == HTTPStatus.BAD_REQUEST, resp.text


@pytest.mark.asyncio
async def test_register_cliente_com_dados_de_perfil(
	db_client: AsyncClient,
	db_engine: AsyncEngine,
):
	payload = _payload()
	payload['cliente'] = {
		'razao_social': 'Cliente Customizado Ltda',
		'cnpj_cpf': f'{uuid.uuid4().int % 10**14:014d}',
		'segmento': 'Marketing',
	}

	resp = await db_client.post('/auth/register', json=payload)

	assert resp.status_code == HTTPStatus.CREATED, resp.text

	async with db_engine.begin() as conn:
		result = await conn.execute(
			text(
				"""
				SELECT razao_social, cnpj_cpf, segmento
				FROM cliente
				WHERE id = :id
				"""
			),
			{'id': resp.json()['id']},
		)

	assert result.one() == (
		payload['cliente']['razao_social'],
		payload['cliente']['cnpj_cpf'],
		payload['cliente']['segmento'],
	)


@pytest.mark.asyncio
async def test_register_funcionario_cria_perfil(
	db_client: AsyncClient,
	db_engine: AsyncEngine,
):
	payload = _funcionario_payload()

	resp = await db_client.post('/auth/register', json=payload)

	assert resp.status_code == HTTPStatus.CREATED, resp.text

	async with db_engine.begin() as conn:
		result = await conn.execute(
			text(
				"""
				SELECT cargo, especialidade
				FROM funcionario
				WHERE id = :id
				"""
			),
			{'id': resp.json()['id']},
		)

	assert result.one() == (
		payload['funcionario']['cargo'],
		payload['funcionario']['especialidade'],
	)


@pytest.mark.asyncio
async def test_me_sem_token_retorna_unauthorized(db_client: AsyncClient):
	resp = await db_client.get('/auth/me')

	assert resp.status_code == HTTPStatus.UNAUTHORIZED, resp.text


@pytest.mark.asyncio
async def test_me_com_token_de_usuario_inexistente_retorna_unauthorized(db_client: AsyncClient):
	token = create_access_token(999_999, 'cliente')

	resp = await db_client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})

	assert resp.status_code == HTTPStatus.UNAUTHORIZED, resp.text


@pytest.mark.asyncio
async def test_refresh_com_usuario_inexistente_retorna_unauthorized(db_client: AsyncClient):
	token = create_refresh_token(999_999)

	resp = await db_client.post('/auth/refresh', json={'refresh_token': token})

	assert resp.status_code == HTTPStatus.UNAUTHORIZED, resp.text

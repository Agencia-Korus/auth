from http import HTTPStatus

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_api(
	client: AsyncClient,
):
	resp = await client.get('/health')
	assert resp.status_code == HTTPStatus.OK
	assert resp.json() == {'status': 'auth api is running...'}

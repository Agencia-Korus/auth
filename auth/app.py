from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.config import get_settings
from auth.controller import router as auth_router

settings = get_settings()

app = FastAPI(title='Korus Auth Sercive', version='0.1.0')

_origens_cors = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(',') if o.strip()]
_liberar_todas_origens = '*' in _origens_cors

app.add_middleware(
	CORSMiddleware,
	allow_origins=[] if _liberar_todas_origens else _origens_cors,
	allow_origin_regex='.*' if _liberar_todas_origens else None,
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)

app.include_router(auth_router)


@app.get('/health', tags=['Health'])
async def health():
	"""Retorna o status básico da API."""
	return {'status': 'auth api is running...'}

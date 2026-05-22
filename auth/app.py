from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.config import get_settings
from auth.controller import router as auth_router

settings = get_settings()

app = FastAPI(title='Korus Auth Sercive', version='0.1.0')

app.add_middleware(
	CORSMiddleware,
	allow_origins=[o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(',')],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)

app.include_router(auth_router)


@app.get('/health', tags=['Health'])
async def health():
	return {'status': 'auth api is running...'}

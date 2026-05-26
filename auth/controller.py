from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from auth.database import get_session
from auth.repository import UsuarioRepository
from auth.schema import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UsuarioInfo
from auth.security import CREDENTIALS_EXCEPTION, TOKEN_TYPE_ACESS, decode_token
from auth.service import AuthService

router = APIRouter(prefix='/auth', tags=['Auth'])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login', auto_error=False)


def _service(session: Annotated[AsyncSession, Depends(get_session)]) -> AuthService:
	"""Cria o serviço de autenticação com a sessão atual."""
	return AuthService(session)


ServiceDep = Annotated[AuthService, Depends(_service)]


async def get_current_user(
	token: Annotated[str | None, Depends(oauth2_scheme)],
	session: Annotated[AsyncSession, Depends(get_session)],
) -> UsuarioInfo:
	"""Resolve o usuário autenticado a partir do token Bearer."""
	if not token:
		raise CREDENTIALS_EXCEPTION
	payload = decode_token(token, TOKEN_TYPE_ACESS)
	repo = UsuarioRepository(session)
	usuario = await repo.get(int(payload['sub']))
	if not usuario:
		raise CREDENTIALS_EXCEPTION
	return UsuarioInfo.model_validate(usuario)


@router.post(
	'/register',
	response_model=UsuarioInfo,
	status_code=status.HTTP_201_CREATED,
	summary='Auto-cadastro público - cria cliente e funcionario pendente',
)
async def register(payload: RegisterRequest, service: ServiceDep):
	"""Registra um novo usuário público."""
	return await service.register(payload)


@router.post('/login', response_model=TokenResponse, summary='Login de usuário ativo')
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], service: ServiceDep):
	"""Autentica usuário ativo e retorna tokens JWT."""
	payload = LoginRequest(email=form_data.username, senha=form_data.password)
	_, tokens = await service.login(payload)
	return tokens


@router.post('/refresh', response_model=TokenResponse)
async def refresh(payload: RefreshRequest, service: ServiceDep):
	"""Renova tokens a partir de um refresh token válido."""
	return await service.refresh(payload.refresh_token)


@router.get('/me', response_model=UsuarioInfo, summary='Obtém o perfil autenticado')
async def me(current_user: Annotated[UsuarioInfo, Depends(get_current_user)]):
	"""Retorna os dados do usuário autenticado."""
	return current_user

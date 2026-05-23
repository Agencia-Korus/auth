from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.model import Admin, Cliente, Funcionario, UserRole, UserStatus, Usuario
from auth.repository import UsuarioRepository
from auth.schema import LoginRequest, RegisterRequest, TokenResponse
from auth.security import (
	TOKEN_TYPE_REFRESH,
	create_access_token,
	create_refresh_token,
	decode_token,
	hash_password,
	verify_password,
)


class AuthService:
	def __init__(self, session: AsyncSession):
		self.session = session
		self.repo = UsuarioRepository(session)

	async def register(self, payload: RegisterRequest) -> Usuario:
		if await self.repo.get_by_email(payload.email):
			raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email já cadastrado')
		if payload.role == UserRole.ADMIN:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=(
					'Auto-cadastro como admin não é permitido. Admins são criados por outro admin'
				),
			)
		usuario = Usuario(
			nome=payload.nome,
			email=payload.email,
			senha_hash=hash_password(payload.senha),
			role=payload.role,
			telefone=payload.telefone,
			status=UserStatus.PENDENTE,
		)
		usuario = await self.repo.add(usuario)
		await self._create_role_profile(usuario, payload)
		await self.session.commit()
		return usuario

	async def _create_role_profile(self, usuario: Usuario, payload: RegisterRequest) -> None:
		if usuario.role == UserRole.CLIENTE:
			cliente = payload.cliente
			razao_social = usuario.nome
			cnpj_cpf = f'auth-{usuario.id}'
			if cliente and cliente.razao_social:
				razao_social = cliente.razao_social
			if cliente and cliente.cnpj_cpf:
				cnpj_cpf = cliente.cnpj_cpf
			self.session.add(
				Cliente(
					id=usuario.id,
					razao_social=razao_social,
					cnpj_cpf=cnpj_cpf,
					segmento=cliente.segmento if cliente else None,
				)
			)
		elif usuario.role == UserRole.FUNCIONARIO:
			funcionario = payload.funcionario
			self.session.add(
				Funcionario(
					id=usuario.id,
					cargo=(
						funcionario.cargo if funcionario and funcionario.cargo else 'Funcionario'
					),
					especialidade=funcionario.especialidade if funcionario else None,
				)
			)
		elif usuario.role == UserRole.ADMIN:
			admin = payload.admin
			self.session.add(Admin(id=usuario.id, nivel_acesso=admin.nivel_acesso if admin else 1))
		await self.session.flush()

	async def login(self, payload: LoginRequest) -> tuple[Usuario, TokenResponse]:
		usuario = await self.repo.get_by_email(payload.email)
		if not usuario or not verify_password(payload.senha, usuario.senha_hash):
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED, detail='Email ou senha inválidos'
			)
		if usuario.status != UserStatus.ATIVO:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN, detail='Usuario inativo ou pendente'
			)
		tokens = TokenResponse(
			access_token=create_access_token(usuario.id, usuario.role.value),
			refresh_token=create_refresh_token(usuario.id),
		)
		return usuario, tokens

	async def refresh(self, refresh_token: str) -> TokenResponse:
		payload = decode_token(refresh_token, TOKEN_TYPE_REFRESH)
		usuario = await self.repo.get(int(payload['sub']))
		if not usuario:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token inválido')
		return TokenResponse(
			access_token=create_access_token(usuario.id, usuario.role.value),
			refresh_token=create_refresh_token(usuario.id),
		)

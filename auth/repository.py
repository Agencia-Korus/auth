from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.model import Usuario


class UsuarioRepository:
	def __init__(self, session: AsyncSession):
		"""Armazena a sessão usada pelas operações de usuário."""
		self.session = session

	async def get(self, usuario_id: int) -> Usuario | None:
		"""Busca um usuário pelo identificador primário."""
		return await self.session.get(Usuario, usuario_id)

	async def get_by_email(self, email: str) -> Usuario | None:
		"""Busca um usuário pelo email cadastrado."""
		stmt = select(Usuario).where(Usuario.email == email)
		result = await self.session.execute(stmt)
		return result.scalar_one_or_none()

	async def add(self, usuario: Usuario) -> Usuario:
		"""Persiste um usuário e atualiza seus campos gerados."""
		self.session.add(usuario)
		await self.session.flush()
		await self.session.refresh(usuario)
		return usuario

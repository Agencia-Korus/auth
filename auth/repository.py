from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.model import Usuario


class UsuarioRepository:
	def __init__(self, session: AsyncSession):
		self.session = session

	async def get(self, usuario_id: int) -> Usuario | None:
		return await self.session.get(Usuario, usuario_id)

	async def get_by_email(self, email: str) -> Usuario | None:
		stmt = select(Usuario).where(Usuario.email == email)
		result = await self.session.execute(stmt)
		return result.scalar_one_or_none()

	async def add(self, usuario: Usuario) -> Usuario:
		self.session.add(usuario)
		await self.session.flush()
		await self.session.refresh(usuario)
		return usuario

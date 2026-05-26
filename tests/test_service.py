import pytest

from auth.model import Admin, UserRole, Usuario
from auth.schema import RegisterRequest
from auth.service import AuthService

ADMIN_ACCESS_LEVEL = 7


class FakeSession:
	def __init__(self):
		"""Inicializa estado capturado pela sessão falsa."""
		self.added = []
		self.flushed = False

	def add(self, item):
		"""Registra objetos adicionados durante o teste."""
		self.added.append(item)

	async def flush(self):
		"""Marca que a sessão falsa recebeu flush."""
		self.flushed = True


@pytest.mark.asyncio
async def test_create_role_profile_admin_cria_perfil_admin():
	"""Garante que o branch interno de perfil admin é criado."""
	session = FakeSession()
	service = AuthService(session)
	usuario = Usuario(id=1, nome='Admin', email='admin@example.com', role=UserRole.ADMIN)
	payload = RegisterRequest(
		nome='Admin',
		email='admin@example.com',
		senha='senha-forte-123',
		role=UserRole.ADMIN,
		admin={'nivel_acesso': ADMIN_ACCESS_LEVEL},
	)

	await service._create_role_profile(usuario, payload)

	assert session.flushed is True
	assert len(session.added) == 1
	assert isinstance(session.added[0], Admin)
	assert session.added[0].nivel_acesso == ADMIN_ACCESS_LEVEL

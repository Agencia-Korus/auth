from datetime import date, datetime
from enum import Enum

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from auth.database import Base

NOME_MAX_LENGTH = 150
SENHA_HASH_MAX_LENGTH = 255
TELEFONE_MAX_LENGTH = 20
AVATAR_MAX_LENGTH = 500
DOCUMENTO_MAX_LENGTH = 20
RAZAO_SOCIAL_MAX_LENGTH = 200
CARGO_MAX_LENGTH = 100
SEGMENTO_MAX_LENGTH = 100


class UserRole(str, Enum):
	CLIENTE = 'cliente'
	FUNCIONARIO = 'funcionario'
	ADMIN = 'admin'


class UserStatus(str, Enum):
	ATIVO = 'ativo'
	INATIVO = 'inativo'
	PENDENTE = 'pendente'


def enum_values(cls: type[Enum]) -> list[str]:
	return [member.value for member in cls]


class Usuario(Base):
	__tablename__ = 'usuario'

	id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
	nome: Mapped[str] = mapped_column(String(NOME_MAX_LENGTH), nullable=False)
	email: Mapped[str] = mapped_column(CITEXT(), unique=True, nullable=False)
	senha_hash: Mapped[str] = mapped_column(String(SENHA_HASH_MAX_LENGTH), nullable=False)
	role: Mapped[UserRole] = mapped_column(
		SAEnum(UserRole, name='user_role', create_type=False, values_callable=enum_values),
		nullable=False,
	)
	avatar: Mapped[str | None] = mapped_column(String(AVATAR_MAX_LENGTH))
	telefone: Mapped[str | None] = mapped_column(String(TELEFONE_MAX_LENGTH))
	status: Mapped[UserStatus] = mapped_column(
		SAEnum(UserStatus, name='user_status', create_type=False, values_callable=enum_values),
		nullable=False,
		default=UserStatus.ATIVO,
	)
	criado_em: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
	atualizado_em: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)


class Cliente(Base):
	__tablename__ = 'cliente'

	id: Mapped[int] = mapped_column(
		BigInteger, ForeignKey('usuario.id', ondelete='CASCADE'), primary_key=True
	)
	razao_social: Mapped[str] = mapped_column(String(RAZAO_SOCIAL_MAX_LENGTH), nullable=False)
	cnpj_cpf: Mapped[str] = mapped_column(
		String(DOCUMENTO_MAX_LENGTH), unique=True, nullable=False
	)
	segmento: Mapped[str | None] = mapped_column(String(SEGMENTO_MAX_LENGTH))


class Funcionario(Base):
	__tablename__ = 'funcionario'

	id: Mapped[int] = mapped_column(
		BigInteger, ForeignKey('usuario.id', ondelete='CASCADE'), primary_key=True
	)
	cargo: Mapped[str] = mapped_column(String(CARGO_MAX_LENGTH), nullable=False)
	especialidade: Mapped[str | None] = mapped_column(String(CARGO_MAX_LENGTH))
	data_admissao: Mapped[date] = mapped_column(
		Date, nullable=False, server_default=func.current_date()
	)
	xp_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
	nivel: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Admin(Base):
	__tablename__ = 'admin'

	id: Mapped[int] = mapped_column(
		BigInteger, ForeignKey('usuario.id', ondelete='CASCADE'), primary_key=True
	)
	nivel_acesso: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
	data_promocao: Mapped[date] = mapped_column(
		Date, nullable=False, server_default=func.current_date()
	)

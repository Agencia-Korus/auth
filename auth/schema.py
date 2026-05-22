from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic_core.core_schema import json_schema

from auth.model import (
    UserRole,
    UserStatus,
    NOME_MAX_LENGTH,
    TELEFONE_MAX_LENGTH,
    DOCUMENTO_MAX_LENGTH,
    RAZAO_SOCIAL_MAX_LENGTH,
    CARGO_MAX_LENGTH,
    SEGMENTO_MAX_LENGTH,
)

SENHA_MIN_LENGTH = 8

class ClientePayload(BaseModel):
    razao_social: str | None = Field(default=None, max_length=RAZAO_SOCIAL_MAX_LENGTH)
    cnpj_cpf: str | None = Field(default=None, max_length=DOCUMENTO_MAX_LENGTH)
    segmento: str | None = Field(default=None, max_length=SEGMENTO_MAX_LENGTH)

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'razao_social': 'Korus Solutions Ltda',
                'cnpj_cpf': '12345678000199',
                'segmento': 'Marketing'
            }
        }
    )


class FuncionarioPayload(BaseModel):
    cargo: str | None = Field(default=None, max_length=CARGO_MAX_LENGTH)
    especialidade: str | None = Field(default=None, max_length=CARGO_MAX_LENGTH)

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'cargo': 'Designer',
                'especialidade': 'Identidade visual'
            }
        }
    )


class AdminPayload(BaseModel):
    nivel_acesso: int = 1


class RegisterRequest(BaseModel):
    nome: str = Field(max_length=NOME_MAX_LENGTH)
    email: EmailStr
    senha: str = Field(min_length=SENHA_MIN_LENGTH)
    role: UserRole = Field(
        default=UserRole.CLIENTE,
        description='Apenas cliente ou funcionário podem se auto-cadastrar'
    )
    telefone: str | None = Field(default=None, max_length=TELEFONE_MAX_LENGTH)
    cliente: ClientePayload | None = None
    funcionario: FuncionarioPayload | None = None
    admin: AdminPayload | None = None

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'nome': 'Korus Solutions Ltda',
                'email': 'contato@korus.com.br',
                'senha': 'SenhaForte@123',
                'role': 'cliente',
                'telefone': '(61) 99999-9999',
                'cliente': {
                    'razao_social': 'Korus Solutions Ltda',
                    'cnpj_cpf': '12345678000199',
                    'segmento': 'Marketing'
                },
                'funcionario': None,
                'admin': None
            }
        }
    )


    class LoginRequest(BaseModel):
        email: EmailStr
        senha: str

        model_config = ConfigDict(
            json_schema_extra={
                'example': {
                    'email': 'admin@email.com',
                    'senha': 'AdminKorus@123'
                }
            }
        )


class RefreshRequest(BaseModel):
    refresh_token: str

    model_config = ConfigDict(
        json_schema_extra={'example': {'refresh_token': 'refresh-token-exemplo'}}
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'Bearer'


class UsuarioInfo(BaseModel):
    id: int
    nome: str
    email: str
    role: UserRole
    status: UserStatus

    model_config = ConfigDict(from_attributes=True)

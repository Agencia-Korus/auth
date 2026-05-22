# Korus Auth Service

Microsserviço de autenticação JWT.

## Endpoints

- `POST /auth/register` — cria um usuário.
- `POST /auth/login` — emite `access_token` + `refresh_token`.
- `POST /auth/refresh` — renova os tokens a partir de um refresh válido.
- `GET /auth/me` — retorna o usuário do token (Bearer).
- `GET /health` — checagem de saúde + ping no DB.

Swagger: `GET /docs`.

## Tokens

- `access_token` carrega `sub` (id), `role` e `type=access`. Expira em `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (padrão 60min).
- `refresh_token` só serve para chamar `/auth/refresh`. Expira em `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (padrão 7 dias).

A `api/` valida o `access_token` com o **mesmo `JWT_SECRET_KEY`** — por isso a env var deve ser compartilhada.

## Rodando

```bash
cp .env.example .env
poetry install
poetry run task run
```

Docker:

```bash
docker build -t korus-auth .
docker run --rm -p 8001:8001 --env-file .env korus-auth
```

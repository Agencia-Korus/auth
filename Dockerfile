# syntax=docker/dockerfile:1

############################
# Stage 1 - builder
############################
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.3.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true

WORKDIR /app

# Instala o Poetry isolado
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# Copia apenas os manifests para aproveitar o cache de camadas
COPY pyproject.toml poetry.lock* ./

# Cria a venv em /app/.venv apenas com dependencias de producao
RUN poetry install --only main --no-root --no-ansi

############################
# Stage 2 - runtime
############################
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Usuario sem privilegios
RUN groupadd --system app && useradd --system --gid app --no-create-home app

# Copia a venv pronta do builder
COPY --from=builder /app/.venv /app/.venv

# Copia o codigo da aplicacao
COPY auth ./auth

USER app

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8001/health').status==200 else sys.exit(1)"

CMD ["uvicorn", "auth.app:app", "--host", "0.0.0.0", "--port", "8001"]

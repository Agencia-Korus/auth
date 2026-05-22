FROM python:3.13-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry \
 && poetry config installer.max-workers 10 \
 && poetry install --no-interaction --no-ansi --without dev --no-root

COPY . .

EXPOSE 8001

CMD ["poetry", "run", "uvicorn", "--host", "0.0.0.0", "--port", "8001", "auth.app:app"]

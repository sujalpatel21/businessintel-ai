FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --locked

COPY . .

EXPOSE 10000

CMD ["uv", "run", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvbin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN /uvbin/uv sync --frozen --no-dev

COPY src/ ./src/
RUN /uvbin/uv build

FROM python:3.11-slim
WORKDIR /app
RUN useradd -m findexuser
USER findexuser

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/dist /app/dist
RUN /app/.venv/bin/pip install /app/dist/*.whl

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["findex", "serve", "--host", "0.0.0.0", "--port", "8000"]
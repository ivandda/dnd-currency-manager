FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set uv to use copy mode (avoids hardlink issues in Docker)
ENV UV_LINK_MODE=copy

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Pre-install production dependencies (cached layer)
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Startup script placed OUTSIDE /app so volume mount can't overwrite it
RUN printf '#!/bin/sh\nset -e\ncd /app\nuv sync --frozen --no-dev\nexec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload\n' > /start.sh \
    && chmod +x /start.sh

EXPOSE 8000

CMD ["/start.sh"]

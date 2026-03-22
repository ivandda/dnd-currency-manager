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

RUN cp /app/docker-entrypoint.sh /usr/local/bin/app-entrypoint \
    && chmod +x /usr/local/bin/app-entrypoint

EXPOSE 8000

CMD ["/usr/local/bin/app-entrypoint"]

# Agent Feng Dockerfile
# Multi-stage build for minimal production image

# ============================================
# Stage 1: Builder - resolve deps and build wheels
# ============================================
FROM python:3.14-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc musl-dev libffi-dev

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy only files needed for dependency resolution
COPY pyproject.toml README.md ./
COPY src/ src/

# Export requirements and download wheels (dependencies only, not the project)
RUN mkdir /wheels && \
    uv export --group slim --no-dev --no-emit-project -o requirements.txt && \
    pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

# ============================================
# Stage 2: Runtime base - dependencies only
# ============================================
FROM python:3.14-alpine AS runtime-base

WORKDIR /app

# Install wheels and strip unnecessary files in single layer
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*.whl && \
    rm -rf /wheels && \
    # Remove pip (not needed at runtime)
    pip uninstall -y pip setuptools && \
    # Remove __pycache__ and .pyc files
    find /usr/local/lib/python3.14 -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.14 -name "*.pyc" -delete 2>/dev/null || true && \
    # Remove unnecessary package metadata
    find /usr/local/lib/python3.14 -type d -name "*.dist-info" -exec sh -c 'cd "$1" && rm -f RECORD WHEEL top_level.txt' _ {} \; 2>/dev/null || true

# Create non-root user
RUN adduser -D -h /app -s /bin/sh agent && \
    chown -R agent:agent /app



# ============================================
# Stage 3: Production - add application code
# ============================================
FROM runtime-base AS production

# Runtime environment (no defaults for overridable vars)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Copy application code (changes frequently, keep last)
COPY --chown=agent:agent src/agent_feng/ /app/agent_feng/
COPY --chown=agent:agent config/ /app/config/

USER agent

CMD ["python", "-m", "agent_feng"]

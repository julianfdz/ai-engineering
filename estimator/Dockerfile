# =============================================================================
# Stage 1 — Builder
# =============================================================================
# We use a multi-stage build so that build tools (uv, compilers, headers) stay
# out of the final image, keeping it small and reducing the attack surface.
FROM python:3.11-slim AS builder

# Install uv — a fast Python package manager written in Rust.
# Copying the static binary from the official image is the fastest method.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifests first. Docker caches each layer, so dependencies
# are only reinstalled when pyproject.toml or uv.lock actually change.
COPY pyproject.toml uv.lock* ./

# Install production dependencies only (no dev tools like pytest/ruff).
# --no-install-project skips installing our own package (we just need deps).
# uv will generate the lockfile if it doesn't exist yet.
RUN uv sync --no-install-project --no-dev

# -----------------------------------------------------------------------------
# LOCAL (fork) — torch CPU + modelo spaCy en español
# -----------------------------------------------------------------------------
# unstructured[all-docs] arrastra torch + torchvision con el runtime CUDA
# (nvidia-*, triton: varios GB) aunque aquí nada corre en GPU. Se cambian por
# las ruedas CPU de la MISMA versión. El guard tolera que torch no esté.
ARG TORCH_CPU_ONLY=true
RUN if [ "$TORCH_CPU_ONLY" = "true" ]; then \
        FREEZE="$(uv pip freeze --python /app/.venv)"; \
        TORCH_VERSION="$(echo "$FREEZE" | sed -n 's/^torch==\([0-9][0-9.]*\).*/\1/p')"; \
        TV_VERSION="$(echo "$FREEZE" | sed -n 's/^torchvision==\([0-9][0-9.]*\).*/\1/p')"; \
        if [ -n "$TORCH_VERSION" ]; then \
            CUDA_PKGS="$(echo "$FREEZE" | cut -d= -f1 | grep -E '^(nvidia-|triton$)' || true)"; \
            uv pip uninstall --python /app/.venv torch torchvision $CUDA_PKGS && \
            uv pip install --python /app/.venv --no-deps \
                --index-url https://download.pytorch.org/whl/cpu \
                "torch==${TORCH_VERSION}" ${TV_VERSION:+"torchvision==${TV_VERSION}"}; \
        fi; \
    fi

# El analyzer de Presidio y el preflight necesitan es_core_news_md, que no está
# en pyproject.toml. El venv de uv no trae pip (spacy download no funciona), así
# que se instala la rueda oficial compatible con spaCy 3.8.x.
RUN uv pip install --python /app/.venv --no-deps \
    "es_core_news_md @ https://github.com/explosion/spacy-models/releases/download/es_core_news_md-3.8.0/es_core_news_md-3.8.0-py3-none-any.whl"


# =============================================================================
# Stage 2 — Runtime
# =============================================================================
# Start from a clean slim image — no build tools, no uv, no cached layers
# from the builder stage. Only the virtual environment is carried over.
FROM python:3.11-slim AS runtime

# Never run containers as root. Create a dedicated user and group so the
# process has minimal filesystem and OS-level privileges.
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --create-home appuser

WORKDIR /app

# Bring in the pre-built virtual environment from the builder stage.
COPY --from=builder /app/.venv /app/.venv

# Copy application source code.
COPY app/ /app/app/

# Ensure the non-root user owns everything it needs to run.
RUN chown -R appuser:appgroup /app

# Put the virtual environment's bin directory first on PATH so `python` and
# `uvicorn` resolve to the versions installed inside the venv.
ENV PATH="/app/.venv/bin:$PATH"
# Print logs immediately instead of buffering — critical for container logging.
ENV PYTHONUNBUFFERED=1
# Don't generate .pyc files at runtime; they add no value inside a container.
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to the non-root user for all subsequent commands and at runtime.
USER appuser

# LOCAL (fork): datos de NLTK para la estrategia sentence_window. El código los
# descarga la primera vez que se usa (necesita internet en mitad de la demo).
RUN python -c "import nltk; nltk.download('punkt_tab', quiet=True); nltk.download('punkt', quiet=True)"

EXPOSE 8000

# Docker-native health check. The orchestrator (Compose, Swarm, K8s) will
# mark the container as unhealthy if this probe fails consecutively.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

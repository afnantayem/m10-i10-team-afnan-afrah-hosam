# Build context: repo root (parent of api/).
#
# In docker-compose.yml this MUST be:
#   build:
#     context: .
#     dockerfile: api/Dockerfile
#
# WHY: api/ uses package-relative imports (e.g. `from .deps import ...`).
# uvicorn must be invoked as `uvicorn api.main:app` from /app (repo root),
# not as `uvicorn main:app` from /app/api. Using `build: ./api` appears to
# work during `docker compose build` but the container crashes at startup:
#   ModuleNotFoundError: No module named 'api'
# because the Python path has no `api` package at /app/api/api.

FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────────────
# gcc / g++ are required to compile any C-extension wheels not available
# as pre-built binaries for linux/amd64 + glibc (e.g. some tokenizer deps).
# Removed after pip install to keep the image lean.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────
# Copy requirements first to maximise Docker layer cache reuse.
# The RUN layer below is only invalidated when requirements.txt changes,
# not on every `COPY api/ /app/api/`.
COPY api/requirements.txt /app/requirements.txt

# Generous timeout + retries for transient PyPI mirror flakes on first-pull
# large wheels (torch, transformers, sentence-transformers ≈ 2 GB total).
RUN pip install --no-cache-dir --timeout 300 --retries 5 -r /app/requirements.txt

# ── spaCy model — pinned URL bypasses the compatibility-table resolver ────
# `python -m spacy download en_core_web_sm` queries the compatibility table
# and constructs a release URL. For some spaCy/pip combinations the resolver
# emits a malformed URL with an empty version segment:
#   .../download/-en_core_web_sm/-en_core_web_sm.tar.gz  →  404
# Pinning the tarball URL directly bypasses the resolver entirely.
# en_core_web_sm 3.7.1 is the compatible model for spaCy 3.7.x.
RUN pip install --no-cache-dir --timeout 300 --retries 5 \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# ── Application source ────────────────────────────────────────────────────
# Copied AFTER pip install so source edits do not bust the dependency layer.
COPY api/ /app/api/

# ── Runtime ──────────────────────────────────────────────────────────────
EXPOSE 8000

# CMD runs from WORKDIR=/app so `api` is a top-level package on sys.path.
# `--host 0.0.0.0` is required — the default 127.0.0.1 is unreachable from
# other containers and from the Compose healthcheck wget/curl probes.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
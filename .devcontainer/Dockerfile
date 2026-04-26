# ─────────────────────────────────────────────
# Dev Container — WEBBER System
# Backend : Python 3.11 + Django 5.1
# Frontend: Node.js 20 LTS + React 18 / Vite 5
# ─────────────────────────────────────────────
FROM python:3.11-slim

# ── System packages ──────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ── Node.js 20 LTS ───────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# ── Python tooling ───────────────────────────
RUN pip install --no-cache-dir --upgrade pip

# ── Default working directory ─────────────────
# The source tree is mounted here by devcontainer.json
WORKDIR /workspace

# Expose Django dev server and Vite HMR
EXPOSE 8000 5173

CMD ["/bin/bash"]

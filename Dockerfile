# Build-only frontend tooling; the runtime contains no Node or npm dependencies.
FROM node:24.18.0-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS styles
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY assets/css assets/css
COPY templates templates
COPY apps apps
COPY static/js static/js
RUN npm run css:build

FROM ghcr.io/astral-sh/uv:0.11.28@sha256:0f36cb9361a3346885ca3677e3767016687b5a170c1a6b88465ec14aefec90aa AS uv
FROM python:3.13.14-slim@sha256:9662417aace5ae7b8e2609cce472b72a8958e134ba372808abe9cc1a0c0125e6 AS runtime
COPY --from=uv /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev
COPY . .
COPY --from=styles /build/static/css/app.css static/css/app.css
RUN uv run --locked --no-dev python scripts/build_static.py
RUN groupadd --gid 10001 maison && useradd --uid 10001 --gid maison --no-create-home maison \
    && mkdir -p /app/media && chown maison:maison /app/media
USER 10001:10001
ENV DJANGO_SETTINGS_MODULE=config.settings.production GUNICORN_BIND=0.0.0.0:8000 UV_CACHE_DIR=/tmp/uv-cache
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "--no-dev", "gunicorn", "--env", "DJANGO_SETTINGS_MODULE=config.settings.production", "--config", "deploy/gunicorn.conf.py", "config.wsgi:application"]

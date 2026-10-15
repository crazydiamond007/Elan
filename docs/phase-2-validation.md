# Phase 2 validation

Executed on 2026-10-13 in WSL Ubuntu, with Python 3.13.14, Django 5.2.18 and native PostgreSQL 18.

| Check | Observed result |
| --- | --- |
| `uv sync --locked` | Passed; lockfile matches project dependencies |
| Local database provisioning | Dedicated role/database created; existing cluster configuration preserved |
| `manage.py migrate` | All foundation migrations applied |
| `manage.py check` | No issues, none silenced |
| `manage.py makemigrations --check --dry-run` | No changes detected |
| `pytest` | **51 passed in 1.18 seconds**, using `config.settings.test` and PostgreSQL |
| `ruff check .` | Passed |
| `ruff format --check .` | Passed; 34 files formatted |
| `uv pip check` | All 14 installed Python packages compatible |
| `npm ci --ignore-scripts` | Clean lockfile installation passed |
| npm dependency audit during clean installation | **0 known vulnerabilities** reported |
| `npm run css:build` | Passed with Tailwind 4.3.0 |
| `npm run css:watch` | Watcher started and compiled successfully |
| Production `collectstatic` | 128 files copied, 384 post-processed |
| Production `check --deploy` | One warning: `security.W004`, HSTS not enabled yet |
| Production-settings HTTP smoke | HTTPS redirect, hashed/gzip asset serving, immutable caching, no-index headers and secure admin CSRF cookie passed |
| Live local preview HTTP smoke | Home, CSS, demo information and admin login all returned HTTP 200 |
| Local secret handling | `.env` has mode `0600` and is ignored by Git |
| Source whitespace | No trailing whitespace in reviewable source files |

The first test run exposed an environment-selection issue and two test/rendering issues; those
were corrected before the final full run. No checks were silenced to obtain the passing result.

Tests cover user/admin access and permissions, protected login/logout, CSP nonce handling,
demo disclosure, safe errors, template escaping, host validation, no-index responses and strict
production configuration. Catalog/cart/checkout tests belong to their later implementation phases.

The production smoke used localhost HTTPS settings with Django's test client, not a real TLS
deployment. The running preview uses local development settings. No browser rendering,
Lighthouse measurement, full Python vulnerability audit or public deployment was performed.

HSTS will be enabled after deployed HTTPS is verified. Public admin abuse protection, deployment
infrastructure, production database credentials/TLS, media hosting and security review remain pending.

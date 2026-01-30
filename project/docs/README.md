# Backend Documentation

## Overview
This backend is a Django 5 + Django REST Framework service for collecting, enriching, and serving news articles. It integrates with NewsAPI.org, stores normalized articles in the database, and exposes a filtered, paginated API for client applications.

## Tech Stack
- Django 5.2
- Django REST Framework
- drf-spectacular (OpenAPI schema + Swagger UI)
- NewsAPI Python client
- fastText (language detection)
- YAKE (keyword extraction)

## Project Structure (backend)
- base/manage.py: Django entrypoint
- base/base: project settings, URLs, ASGI
- base/news: app with models, API, providers, services, and commands
- docs/: documentation (this folder)

## Key Endpoints
- /api/news/ — filtered news retrieval
- /api/schema/ — OpenAPI schema (JSON)
- /api/schema/swagger-ui/ — Swagger UI

## Configuration (.env)
The environment file lives at base/.env and is read by base/base/settings.py.

Required settings (production):
- DEBUG
- SECRET_KEY
- ALLOWED_HOSTS
- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_HOST
- POSTGRES_PORT
- NEWSAPI_API_KEY

Notes:
- In DEBUG mode, SQLite is used (base/db.sqlite3).
- In non-DEBUG mode, PostgreSQL is used.
- FASTTEXT_MODEL_PATH is defined in settings but the detection helper uses the default model path unless passed explicitly.

## Pagination
Default pagination is DRF PageNumberPagination with a page size of 50 (see REST_FRAMEWORK in settings).

## Where to Read More
- Filtering behavior: docs/filtering.md
- Language detection: docs/language-detection.md
- Management commands: docs/management-commands.md
- Architecture & data model: docs/architecture.md

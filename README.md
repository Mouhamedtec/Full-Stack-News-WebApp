# Full-Stack News WebApp

A full-stack news collection, enrichment, and delivery platform:
- Backend: Django 5 + Django REST Framework service that ingests and normalizes news articles from NewsAPI.org, enriches articles (language detection, keywords), and exposes a filtered, paginated API.
- Frontend: Angular standalone components that consume the backend API and provide a responsive news UI.

This README summarizes the project, how components fit together, and how to get the app running for local development.

---

## Table of contents

- [Features](#features)
- [Architecture & components](#architecture--components)
- [Tech stack](#tech-stack)
- [Getting started (development)](#getting-started-development)
  - [Prerequisites](#prerequisites)
  - [Backend (Django) — quick start](#backend-django---quick-start)
  - [Frontend (Angular) — quick start](#frontend-angular---quick-start)
  - [Running with Docker (if available)](#running-with-docker-if-available)
- [Configuration / Environment](#configuration--environment)
- [Management & background tasks](#management--background-tasks)
- [API docs & important endpoints](#api-docs--important-endpoints)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Features

- Periodic ingestion of news sources and articles via NewsAPI.
- Normalization and storage of article metadata.
- Language detection using fastText.
- Keyword extraction (YAKE).
- Filtered and paginated news API for client applications.
- Angular-based frontend with instant search and filters.

---

## Architecture & components

- backend/
  - base/ — Django project
    - base/asgi.py — ASGI entrypoint
    - base/settings.py — Django settings (CORS, NewsAPI key, fastText model path, etc.)
  - base/news — core Django app:
    - models, serializers, views, provider integrations, services (language detection, keyword extraction), and management commands
  - docs/ — developer docs:
    - architecture.md, language-detection.md, management-commands.md, and other notes
  - entrypoint.sh — example entrypoint that runs `uvicorn base.asgi:application` for ASGI hosting
- backend/news-frontend/ — Angular frontend (standalone component approach)
  - src/ — Angular source including `app`, `news-list` component, `environments.ts` (apiBaseUrl), etc.

Key design notes:
- The backend exposes a JSON API consumed by the frontend.
- Language detection uses a fastText model (`lid.176.ftz`) loaded by a thread-safe singleton loader.
- Background ingestion and provider sync tasks are implemented as Django management commands.

---

## Tech stack

- Backend
  - Python, Django 5.x
  - Django REST Framework
  - drf-spectacular (OpenAPI / Swagger)
  - fastText (language detection)
  - YAKE (keyword extraction)
  - NewsAPI Python client
- Frontend
  - Angular (standalone components)
  - Vitest for unit tests (optional)
- Deployment / runtime
  - ASGI server (example: uvicorn used in entrypoint.sh)

---

## Getting started (development)

### Prerequisites

- Python (3.10/3.11+ recommended for Django 5)
- pip
- Node.js (LTS recommended) and npm / pnpm / yarn for the Angular app
- (Optional) Docker for containerized runs
- fastText native or wheel package for language detection (or adjust settings to disable/skip fastText in development)

### Backend (Django) — quick start

1. Clone the repository
   - git clone https://github.com/Mouhamedtec/Full-Stack-News-WebApp.git
2. Create and activate a virtual environment
   - python -m venv .venv && source .venv/bin/activate
3. Install Python dependencies
   - pip install -r backend/requirements.txt
     - If fastText is required, install the appropriate wheel (see backend/docs/language-detection.md)
4. Configure environment variables (see [Configuration](#configuration--environment))
5. Apply migrations and create a superuser
   - cd backend
   - python manage.py migrate
   - python manage.py createsuperuser
6. Run the development server
   - python manage.py runserver 0.0.0.0:8000
   - OR use the ASGI entrypoint (example)
     - ./backend/entrypoint.sh
       - Note: the example entrypoint runs uvicorn on port 8282; you can adapt that as needed.

Notes:
- The backend includes management commands for fetching provider sources and ingestion; see [Management & background tasks](#management--background-tasks).

### Frontend (Angular) — quick start

1. Go to the frontend package
   - cd backend/news-frontend
2. Install dependencies
   - npm install
3. Start the dev server
   - ng serve
   - The Angular dev server runs by default at http://localhost:4200
4. Default frontend environment points to:
   - apiBaseUrl: `http://localhost:8000` (see src/environments/environments.ts)
   - Ensure the backend is running at that address or update the environment file.

CORS:
- The backend CORS settings include `http://localhost:4200` by default, so the frontend can communicate with the backend during development.

### Running with Docker (if available)

This repository includes an ASGI entrypoint (entrypoint.sh) intended for containerized runs. If you prefer Docker:
- Build an image that installs Python deps, copies the app, and uses entrypoint.sh to start uvicorn.
- Ensure environment variables (NEWSAPI_API_KEY, FASTTEXT_MODEL_PATH, DB settings, etc.) are provided to the container.

---

## Configuration / Environment

Important environment variables (examples):
- NEWSAPI_API_KEY — API key for NewsAPI.org (required for ingestion & provider commands)
- FASTTEXT_MODEL_PATH — path to fastText model file (default set to backend/base/news/services/language_detect/models/lid.176.ftz)
- DJANGO_SECRET_KEY, DATABASE_URL, etc. — standard Django settings as needed

Configuration locations:
- backend/base/base/settings.py — project settings, including CORS_ALLOWED_ORIGINS and FASTTEXT_MODEL_PATH
- backend/news-frontend/src/environments/environments.ts — frontend apiBaseUrl

See backend/docs/ for more in-depth docs, including language detection and architecture explanations.

---

## Management & background tasks

Useful management commands:
- fetch_provider_sources
  - Purpose: Pull source metadata from NewsAPI and upsert Source records.
  - Example: python manage.py fetch_provider_sources --once
  - Options: --interval, --category, --language, --country, --once
  - Requires NEWSAPI_API_KEY
- Other ingestion commands: see backend/base/news/management/commands for available tasks.

The backend is designed to run ingestion and provider syncs as long-running commands (they can spawn threads per category and include retry logic).

---

## API docs & important endpoints

- /api/news/ — filtered news retrieval (main client endpoint)
- /api/schema/ — OpenAPI schema (JSON)
- /api/schema/swagger-ui/ — Swagger UI (interactive API documentation)

Explore the Swagger UI to see available query parameters, serializers, and example responses.

---

## Testing

- Backend: Use Django test runner (python manage.py test) for backend tests.
- Frontend: The Angular project is configured to run unit tests with Vitest (see backend/news-frontend/README.md).
- For end-to-end testing, run `ng e2e` (select an e2e runner as needed).

---

## Contributing

Contributions are welcome. Suggested steps:
1. Open an issue describing the change or feature.
2. Create a branch from main for your work.
3. Send a pull request with a clear description and tests where appropriate.
4. For backend changes, update or add docs under backend/docs/.

If you want, I can open a PR that replaces the repository README with this content — tell me the branch name and whether to use the default branch as base.

---

## License

This repository does not include a LICENSE file (or the license is not documented here). Please add a LICENSE (e.g., MIT) if you want to make the project permissively licensed.

---

## Contact

Maintainer: repository owner (Mouhamedtec)

---

Thanks — tell me if you'd like:
- A PR created that replaces the root README.md with this version,
- Any wording changes, or
- A shorter README (summary) plus a longer developer-oriented CONTRIBUTING or DEVELOPER doc.

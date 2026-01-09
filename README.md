# ChatLab (Humanlike Chatbot)

ChatLab is a dockerized research chat lab for running configurable, LLM-backed chat experiments. It includes a Django API/admin, a React chat UI, MariaDB, Redis, and Sphinx docs. Secrets and service credentials live in `.env`, while LLM provider selection and bot personas are managed through the Django admin UI.

## Quick start (local)

Prereqs: Docker Engine, Docker Compose, Git.

1. Copy the env file and set values (at minimum: `SECRET_KEY` and your API keys):

   ```bash
   cp sample.env .env
   ```

2. Build and start services:

   ```bash
   make start
   # or: docker compose up --build
   ```

3. Create an admin user (one-time):

   ```bash
   docker exec -it humanlike-chatbot-backend-1 bash
   python manage.py createsuperuser
   ```

4. Open:
   - Chat UI: <http://localhost:3000>
   - Admin/API: <http://localhost:8000/api/admin/>
   - Docs: <http://localhost:8001>

## Configuration

- `.env` holds secrets and service credentials (see `sample.env`).
- LLM provider selection and bot personas are configured in the Django admin UI.

## Repo layout

- `generic_chatbot/` - Django backend + LLM integration
- `generic_chatbot_frontend/` - React chat UI
- `chatlab/docs/` - Sphinx docs
- `docker-compose.yml` - local dev stack

## Common commands

- `make start` - build and run all services
- `make stop` - stop services
- `make stop-clean` - stop and remove volumes
- `make test` - run backend tests (containers must be running)
- `make lint` - run backend + frontend lint/format

## Docs

Sphinx docs live in `chatlab/docs` and are served by the `docs` service on port 8001 when running `make start`.

## Deployment & CI/CD

- Local dev uses Docker Compose (`docker-compose.yml`).
- AWS production path: Elastic Beanstalk (backend), RDS, ElastiCache/Redis, S3 + CloudFront (frontend). See `chatlab/docs/deployment/aws-deployment.rst`.
- GitHub Actions deploy on push:
  - `staging` branch -> staging AWS (`.github/workflows/staging.yml`)
  - `main` branch -> production AWS (`.github/workflows/production.yml`)

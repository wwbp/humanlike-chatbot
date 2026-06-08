# Humanlike Chatbot

A research platform for running configurable, LLM-backed chat experiments. Researchers configure bots and personas through a Django admin UI; participants interact via an embeddable React chat UI.

## Stack

| Layer | Tech |
|-------|------|
| API | Django 5 + Django REST Framework |
| Frontend | React 18 + Vite |
| Database | MariaDB |
| Cache | Redis |
| LLM | AWS Bedrock, OpenAI, Anthropic (configurable per bot) |
| Deploy | AWS Elastic Beanstalk (API) + S3/CloudFront (frontend) |

## Repo layout

```
api/        Django backend — models, views, LLM engines, admin
web/        React frontend — chat UI
infra/      Terraform (separate test environment, not production)
```

## Local setup

**Prerequisites:** Docker, Docker Compose, Make

```bash
cp api/.env.example api/.env    # fill in SECRET_KEY, DB passwords, and at least one LLM key
cp web/.env.example web/.env    # set VITE_API_URL if needed
make up                         # builds and starts all services
make migrate                    # run DB migrations
make superuser                  # create admin user from DJANGO_SUPERUSER_* in api/.env
```

| Service | URL |
|---------|-----|
| Chat UI | http://localhost:3000 |
| Admin / API | http://localhost:8000/api/admin/ |

## Common commands

```bash
make up             # build and start all services
make down           # stop services
make reset          # stop and wipe volumes (fresh DB)
make migrate        # run Django migrations
make superuser      # create admin user (reads DJANGO_SUPERUSER_* from api/.env)
make shell          # Django shell
make test           # run all tests (backend + frontend)
make coverage       # backend tests with coverage report
make lint           # ruff + isort + eslint + prettier
```

## Configuration

Secrets and service config live in `api/.env` and `web/.env` — copy from the `.env.example` files in each directory. Key variables:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret key (required) |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | LLM provider keys (at least one required) |
| `DATABASE_*` / `MYSQL_*` | DB connection + MariaDB container config |
| `DJANGO_SUPERUSER_*` | Admin credentials created by `make superuser` |

Bot prompts, personas, LLM model selection, and moderation settings are managed in the Django admin UI at `/api/admin/`.

## Deployment

Push to a branch to trigger GitHub Actions:

| Branch | Target |
|--------|--------|
| `staging` | Staging environment (`dev.bot.wwbp.org`) |
| `main` | Production (`bot.wwbp.org`) |

Both deploy the frontend to S3/CloudFront and the backend to Elastic Beanstalk. CI (lint + tests) must pass before deploy.

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
cp api/.env.example api/.env    # fill in SECRET_KEY and at least one LLM API key
cp web/.env.example web/.env    # set VITE_API_URL if needed
make start                      # builds and starts all services
```

First run only — create an admin user:
```bash
docker exec -it humanlike-chatbot-backend-1 python manage.py createsuperuser
```

| Service | URL |
|---------|-----|
| Chat UI | http://localhost:3000 |
| Admin / API | http://localhost:8000/api/admin/ |

## Common commands

```bash
make start          # build and start all services
make stop           # stop services
make stop-clean     # stop and remove volumes (wipes DB)
make test           # run backend tests (containers must be running)
make test-coverage  # backend tests with coverage report
make migrate        # run Django migrations
make shell          # Django shell
make lint           # ruff + isort + eslint + prettier
```

## Configuration

All secrets and service URLs live in `.env` (see `sample.env`). Bot prompts, personas, LLM model selection, and moderation settings are managed in the Django admin UI at `/api/admin/`.

## Deployment

Push to a branch to trigger GitHub Actions:

| Branch | Target |
|--------|--------|
| `staging` | Staging environment (`dev.bot.wwbp.org`) |
| `main` | Production (`bot.wwbp.org`) |

Both deploy the frontend to S3/CloudFront and the backend to Elastic Beanstalk. CI (lint + tests) must pass before deploy.

COMPOSE = docker compose -f .devcontainer/docker-compose.yml
BACKEND = docker exec humanlike-chatbot-backend-1

define require_up
	@$(COMPOSE) ps | grep -q "Up" || (echo "Services not running — run 'make up' first" && exit 1)
endef

.PHONY: up down reset migrate shell superuser test test-api test-web coverage lint

# ── Dev lifecycle ──────────────────────────────────────────────────────────────

up:
	@$(COMPOSE) ps | grep -q "Up" && echo "Already running" || $(COMPOSE) up --build -d

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v

migrate:
	$(call require_up)
	$(BACKEND) python manage.py migrate

shell:
	$(call require_up)
	docker exec -it humanlike-chatbot-backend-1 python manage.py shell

superuser:
	$(call require_up)
	@docker exec \
		-e DJANGO_SUPERUSER_USERNAME=$$(grep '^DJANGO_SUPERUSER_USERNAME=' api/.env | cut -d= -f2) \
		-e DJANGO_SUPERUSER_EMAIL=$$(grep '^DJANGO_SUPERUSER_EMAIL=' api/.env | cut -d= -f2) \
		-e DJANGO_SUPERUSER_PASSWORD=$$(grep '^DJANGO_SUPERUSER_PASSWORD=' api/.env | cut -d= -f2) \
		humanlike-chatbot-backend-1 \
		python manage.py createsuperuser --noinput

# ── Tests ──────────────────────────────────────────────────────────────────────

test: test-api test-web

test-api:
	$(call require_up)
	$(BACKEND) bash -c "DJANGO_SETTINGS_MODULE=generic_chatbot.settings pytest"

test-web:
	cd web && npm test -- --run

coverage:
	$(call require_up)
	$(BACKEND) bash -c "DJANGO_SETTINGS_MODULE=generic_chatbot.settings pytest --cov=chatbot --cov-report=term-missing --cov-report=html:htmlcov"

# ── Quality ────────────────────────────────────────────────────────────────────

lint:
	$(call require_up)
	$(BACKEND) bash -c "./lint.sh"
	cd web && npm run lint:fix && npm run format

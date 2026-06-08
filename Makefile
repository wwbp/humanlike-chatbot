COMPOSE = docker compose -f .devcontainer/docker-compose.yml

start:
	@if $(COMPOSE) ps | grep -q "Up"; then \
		echo "Containers are already running"; \
	else \
		$(COMPOSE) up --build -d; \
	fi

stop:
	$(COMPOSE) down

stop-clean:
	$(COMPOSE) down -v

test:
	@if $(COMPOSE) ps | grep -q "Up"; then \
		docker exec humanlike-chatbot-backend-1 bash -c "cd /app && DJANGO_SETTINGS_MODULE=generic_chatbot.settings pytest"; \
	else \
		echo "Containers are not running. Please run 'make start' first."; \
	fi

test-coverage:
	@if $(COMPOSE) ps | grep -q "Up"; then \
		docker exec humanlike-chatbot-backend-1 bash -c "cd /app && DJANGO_SETTINGS_MODULE=generic_chatbot.settings pytest --cov=chatbot --cov-report=term-missing --cov-report=html:htmlcov"; \
	else \
		echo "Containers are not running. Please run 'make start' first."; \
	fi

migrate:
	@if $(COMPOSE) ps | grep -q "Up"; then \
		docker exec humanlike-chatbot-backend-1 bash -c "cd /app && python manage.py migrate"; \
	else \
		echo "Containers are not running. Please run 'make start' first."; \
	fi

shell:
	@if $(COMPOSE) ps | grep -q "Up"; then \
		docker exec -it humanlike-chatbot-backend-1 bash -c "cd /app && python manage.py shell"; \
	else \
		echo "Containers are not running. Please run 'make start' first."; \
	fi

lint:
	@if $(COMPOSE) ps | grep -q "Up"; then \
		docker exec humanlike-chatbot-backend-1 bash -c "cd /app && ./lint.sh"; \
	else \
		echo "Containers are not running. Please run 'make start' first."; \
	fi
	@cd web && npm run lint:fix && npm run format

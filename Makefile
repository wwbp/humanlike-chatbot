.PHONY: start stop lint test makemigrations migrate

# Start the application
start:
	docker compose up

# Stop the application
stop:
	docker compose down

# Run linting and code quality checks
lint:
	docker compose exec backend ruff check .

# Run tests
test:
	docker compose exec backend python run_tests.py all

# Create database migrations
makemigrations:
	docker compose exec backend python manage.py makemigrations

# Apply database migrations
migrate:
	docker compose exec backend python manage.py migrate

.PHONY: start stop lint test makemigrations migrate test-coverage test-unit test-integration

# Start the application
start:
	docker compose up

# Stop the application
stop:
	docker compose down

# Run linting and code quality checks
lint:
	docker compose exec backend ruff check .

# Run all tests
test:
	docker compose exec backend python -m pytest

# Run tests with coverage
test-coverage:
	docker compose exec backend python -m pytest --cov=chatbot --cov=server --cov-report=term-missing --cov-report=html

# Run unit tests only
test-unit:
	docker compose exec backend python -m pytest -m "not integration and not slow"

# Run integration tests only
test-integration:
	docker compose exec backend python -m pytest -m "integration"

# Create database migrations
makemigrations:
	docker compose exec backend python manage.py makemigrations

# Apply database migrations
migrate:
	docker compose exec backend python manage.py migrate

# Clean up test artifacts
clean:
	docker compose exec backend find . -type f -name "*.pyc" -delete
	docker compose exec backend find . -type d -name "__pycache__" -delete
	docker compose exec backend rm -rf htmlcov/ .coverage coverage.xml

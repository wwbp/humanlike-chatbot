.PHONY: lint test makemigrations migrate collectstatic clean-tests run-consolidated-tests

# Run linting and code quality checks
lint:
	./run_ruff.sh

# Run consolidated test suite
test: run-consolidated-tests

# Run the consolidated test suite (our new approach)
run-consolidated-tests:
	docker compose run --rm backend python run_tests.py all

# Run specific test
test-specific:
	docker compose run --rm backend python run_tests.py test $(TEST_NAME)

# Run tests with coverage
test-coverage:
	docker compose run --rm backend python run_tests.py coverage

# Create database migrations
makemigrations:
	docker compose run --rm backend python manage.py makemigrations

# Apply database migrations
migrate:
	docker compose run --rm backend python manage.py migrate

# Collect static files
collectstatic:
	docker compose run --rm backend python manage.py collectstatic --noinput

# Clean up scattered test files (after consolidation)
clean-tests:
	@echo "🧹 Cleaning up scattered test files..."
	rm -rf tests/unit/
	rm -rf tests/e2e/
	rm -rf tests/integration/
	@echo "✅ Test cleanup completed. Using consolidated test approach."

# Show test help
test-help:
	docker compose run --rm backend python run_tests.py help

# Quick test run (fastest)
test-quick:
	docker compose run --rm backend python run_tests.py test TestCoreChatFunctionality

# Full test suite with verbose output
test-verbose:
	docker compose run --rm backend python -v run_tests.py all

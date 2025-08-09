# Testing Strategy for Humanlike Chatbot

This document outlines the comprehensive testing strategy for the Django chatbot application.

## 🎯 Testing Philosophy

We follow a **test-driven development** approach with these principles:
- **Test critical paths first** - Core chat functionality, AI integration, database operations
- **Mock external dependencies** - LLM APIs, external services, file systems
- **Comprehensive coverage** - Aim for >80% code coverage
- **Fast feedback** - Unit tests should run in seconds, integration tests in minutes
- **Realistic scenarios** - Test with production-like data and configurations

## 🏗️ Testing Architecture

### Test Categories

1. **Unit Tests**
   - Fast, isolated tests for individual functions
   - Mock all external dependencies
   - Test edge cases and error conditions
   - Marked with `@pytest.mark.unit`

2. **Integration Tests**
   - Test component interactions
   - Use test database with real models
   - Mock external APIs but test internal flows
   - Marked with `@pytest.mark.integration`

3. **End-to-End Tests**
   - Full system tests
   - Test complete user workflows
   - Use test containers for external services
   - Marked with `@pytest.mark.e2e`

### Test Organization

```
tests/
├── conftest.py          # Global pytest configuration
├── factories.py         # Test data factories
├── test_post_processing.py  # Unit tests
├── test_moderation.py       # Unit tests
├── test_runchat.py          # Unit tests
├── test_engine.py           # Unit tests
├── test_chat_flow.py        # Integration tests
├── test_followup_e2e.py     # End-to-end tests
├── test_followup.py         # Unit tests
├── test_core_functionality.py # Core functionality tests
├── test_config.py            # Configuration tests
└── fixtures/           # Test data fixtures
```

## 🚀 Running Tests

### Prerequisites

```bash
# Install development dependencies
make install-dev

# Or manually
pipenv install --dev
```

### Basic Commands

```bash
# Run all tests
make test

# Run specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-e2e          # End-to-end tests only

# Run with coverage
make test-coverage

# Run specific test file
make test-file FILE=tests/test_runchat.py

# Run tests with specific marker
make test-marker MARKER=unit
```

### Docker Testing

```bash
# Run tests inside Docker container
make docker-test

# Or manually
docker-compose exec backend pytest
```

### Advanced Options

```bash
# Verbose output
make test-verbose

# Stop on first failure
make test-failfast

# Show local variables on failure
make test-locals

# Generate HTML coverage report
make test-html

# Run tests in parallel
make test-parallel
```

## 🧪 Writing Tests

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from chatbot.services.runchat import run_chat_round

class TestRunChat:
    """Test the core chat functionality service."""
    
    @pytest.mark.unit
    def test_successful_chat_round(self):
        """Test successful chat round execution."""
        # Arrange
        mock_bot = Mock()
        mock_bot.prompt = "You are a helpful assistant."
        
        # Act
        result = run_chat_round(mock_bot, "Hello!")
        
        # Assert
        assert result is not None
        assert "Hello" in result
```

### Test Markers

Use appropriate markers to categorize tests:

```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Component interaction tests
@pytest.mark.e2e          # Full system tests
@pytest.mark.slow         # Slow running tests
@pytest.mark.external     # Tests with external API calls
@pytest.mark.database     # Database-dependent tests
```

### Mocking Strategy

```python
# Mock external APIs
@patch("chatbot.services.moderation.OpenAI")
def test_moderation_service(self, mock_openai):
    mock_client = Mock()
    mock_openai.return_value = mock_client
    # ... test logic

# Mock database operations
@patch("chatbot.services.runchat.sync_to_async")
async def test_database_operations(self, mock_sync):
    mock_sync.return_value.return_value = mock_data
    # ... test logic
```

### Test Data Factories

Use factory-boy for creating test data:

```python
from tests.factories import BotFactory, PersonaFactory

def test_bot_with_persona():
    bot = BotFactory(prompt="You are helpful.")
    persona = PersonaFactory(name="Friendly", instructions="Be nice!")
    bot.personas.add(persona)
    
    assert len(bot.personas.all()) == 1
```

## 📊 Coverage Requirements

- **Minimum coverage**: 70% (configurable in pytest.ini)
- **Critical paths**: Must have >90% coverage
- **New features**: Must include tests before merge

### Coverage Reports

```bash
# Generate coverage report
make test-coverage

# View HTML report
make test-coverage-open

# Generate coverage badge
make test-badge
```

## 🔧 Test Configuration

### Environment Variables

Tests use these environment variables:
- `DEBUG=True`
- `SECRET_KEY=test-secret-key`
- `DATABASE_ENGINE=django.db.backends.sqlite3`
- `DATABASE_NAME=:memory:`

### Database Configuration

- **Unit tests**: Use in-memory SQLite
- **Integration tests**: Use test database with migrations
- **E2E tests**: Use test containers (MySQL, Redis)

## 🚨 Common Issues & Solutions

### Import Errors

```bash
# Ensure Django settings are configured
export DJANGO_SETTINGS_MODULE=generic_chatbot.settings

# Or use the Makefile
make test-django
```

### Database Connection Issues

```bash
# Wait for database to be ready
make wait-for-db

# Run migrations
python manage.py migrate
```

### Mock Issues

```python
# Ensure mocks are applied to the right import path
@patch("chatbot.services.runchat.OpenAI")  # Correct
# NOT @patch("OpenAI")  # Wrong
```

## 📈 Continuous Integration

### GitHub Actions

Tests run automatically on:
- Every push to main/develop
- Every pull request
- Scheduled runs (nightly)

### Test Stages

1. **Linting** - Code quality checks
2. **Unit Tests** - Fast feedback
3. **Integration Tests** - Component testing
4. **Security Checks** - Vulnerability scanning
5. **Docker Tests** - Container validation

### Failure Handling

- Tests must pass before merge
- Coverage requirements enforced
- Security issues block deployment
- Detailed failure reports generated

## 🎯 Testing Priorities

### Phase 1: Critical Path (Complete)
- ✅ Post-processing service (message chunking)
- ✅ Moderation service (content filtering)
- ✅ Core chat functionality (runchat service)
- ✅ AI engine integration

### Phase 2: Core Components (In Progress)
- 🔄 Database models and operations
- 🔄 API endpoints and views
- 🔄 Authentication and permissions
- 🔄 Error handling and logging

### Phase 3: Advanced Features (Planned)
- 📋 Voice chat functionality
- 📋 File upload and management
- 📋 Bot management and configuration
- 📋 Analytics and reporting

### Phase 4: Performance & Security (Planned)
- 📋 Load testing and performance
- 📋 Security vulnerability testing
- 📋 Penetration testing
- 📋 Compliance testing

## 🤝 Contributing to Tests

### Adding New Tests

1. **Identify the component** to test
2. **Choose appropriate test category** (unit/integration/e2e)
3. **Write test cases** covering:
   - Happy path scenarios
   - Edge cases and error conditions
   - Performance considerations
4. **Add appropriate markers** and documentation
5. **Ensure coverage** meets requirements

### Test Review Checklist

- [ ] Tests are properly categorized and marked
- [ ] All code paths are covered
- [ ] External dependencies are mocked
- [ ] Test data is realistic and varied
- [ ] Error conditions are tested
- [ ] Performance impact is minimal
- [ ] Documentation is clear and complete

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [factory-boy](https://factoryboy.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Mock Library](https://docs.python.org/3/library/unittest.mock.html)

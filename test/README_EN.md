# WildOS VPN Testing System

Comprehensive testing system for the WildOS VPN platform, ensuring reliability and quality of all system components.

## 🏗️ Testing Architecture

The system uses a multi-layered testing architecture:

### 📋 Test Types

- **Unit Tests** (`unit/`) - Isolated testing of individual components
- **Integration Tests** (`integration/`) - Testing component interactions
- **Contract Tests** (`contract/`) - API and gRPC interface contracts
- **E2E Tests** (`e2e/`) - End-to-end full user scenarios
- **Functional Tests** (`functional/`) - Business logic validation

### 🔧 Testing Tools

#### Backend Testing (Python)
- **pytest** - Main testing framework
- **pytest-asyncio** - Asynchronous testing support
- **httpx** - HTTP client for API tests
- **unittest.mock** - Dependency mocking

#### Frontend Testing (TypeScript/JavaScript)
- **Vitest** - Fast unit test runner for Vue/React
- **Playwright** - Browser E2E testing
- **Jest** - Alternative testing framework (legacy)

#### Code Coverage Tools
- **coverage.py** - Python code coverage analysis
- **Istanbul** - JavaScript/TypeScript code coverage

## 📁 Project Structure

```
test/
├── config/           # Configuration files
│   ├── pytest.ini          # Pytest configuration
│   ├── jest.config.js       # Jest configuration
│   ├── playwright.config.ts # Playwright configuration
│   ├── vitest.config.ts     # Vitest configuration
│   ├── global-setup.ts      # Global test setup
│   └── global-teardown.ts   # Global test teardown
├── fixtures/         # Test data and fixtures
│   ├── data_fixtures.py     # Test data fixtures
│   ├── grpc_fixtures.py     # gRPC specific fixtures
│   ├── configs/             # Test configurations
│   ├── data/                # Test data
│   ├── nodes/               # Node data for tests
│   └── users/               # User data
├── unit/             # Unit tests
│   ├── app/                 # Main application tests
│   ├── dashboard/           # Dashboard tests
│   └── wildosnode/          # WildOS node tests
├── integration/      # Integration tests
│   ├── api/                 # API integration tests
│   ├── database/            # Database tests
│   ├── grpc/                # gRPC integration tests
│   └── middleware/          # Middleware tests
├── contract/         # Contract tests
│   ├── api/                 # API contracts
│   └── grpc/                # gRPC contracts
├── e2e/              # End-to-end tests
│   ├── backend/             # Backend E2E tests
│   ├── frontend/            # Frontend E2E tests
│   └── full_stack/          # Full-stack E2E tests
├── functional/       # Functional tests
│   └── e2e/                 # Functional E2E tests
├── conftest.py       # Global pytest fixtures
├── pytest.ini       # Main pytest configuration
└── utils.py          # Testing utilities
```

## 🚀 Running Tests

### All Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with code coverage
pytest --cov=app --cov-report=html
```

### Unit Tests
```bash
# All unit tests
pytest test/unit/

# Specific module
pytest test/unit/app/test_models/

# Specific test
pytest test/unit/app/test_models/test_user_model.py::test_user_creation
```

### Integration Tests
```bash
# All integration tests
pytest test/integration/

# API tests
pytest test/integration/api/

# gRPC tests
pytest test/integration/grpc/
```

### E2E Tests
```bash
# Playwright tests
npx playwright test

# Run in specific browser
npx playwright test --project=chromium

# Run with UI
npx playwright test --ui
```

### Frontend Unit Tests
```bash
# Vitest tests
npm run test

# Jest tests (legacy)
npm run test:jest

# Tests with coverage
npm run test:coverage
```

## 🏷️ Test Markers

The system uses pytest markers for test categorization:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.contract` - Contract tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.grpc` - gRPC related tests
- `@pytest.mark.api` - API tests
- `@pytest.mark.database` - Database tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.requires_db` - Tests requiring database
- `@pytest.mark.requires_grpc` - Tests requiring gRPC server

### Running by Markers
```bash
# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Combination of markers
pytest -m "api and not slow"
```

## 🔧 Configuration

### Test Environment Variables
```bash
TESTING=1
DATABASE_URL=sqlite:///:memory:
SECRET_KEY=test-secret-key-for-testing-only
JWT_SECRET_KEY=test-jwt-secret-key-for-testing-only
DEBUG=False
DOCS=False
```

### Test Ports
- Backend API: `8000`
- Frontend Dev Server: `3000`
- gRPC Server: `8080`

## 📊 Code Coverage

The system requires minimum 80% code coverage:

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Coverage Targets
- **Overall Coverage**: 80%
- **Branch Coverage**: 80%
- **Function Coverage**: 80%
- **Line Coverage**: 80%

## 🔬 Fixtures and Test Data

### Main Fixtures
- `sample_user_data` - User data
- `sample_admin_data` - Admin data
- `sample_node_data` - Node data
- `sample_service_data` - Service data
- `mock_logger` - Mock logger
- `mock_redis` - Mock Redis client
- `async_client` - Async HTTP client

### Using Fixtures
```python
def test_user_creation(sample_user_data):
    user = User(**sample_user_data)
    assert user.username == "testuser"
    assert user.is_active is True
```

## 🐛 Debugging Tests

### Running with Debug
```bash
# Stop on first failure
pytest -x

# Detailed error output
pytest --tb=long

# Run specific test with debug
pytest -s test/unit/app/test_models/test_user_model.py::test_user_creation
```

### Logging in Tests
```python
import logging
logger = logging.getLogger(__name__)

def test_something():
    logger.info("Test started")
    # test code
    logger.info("Test completed")
```

## 📈 CI/CD Integration

Tests are integrated into CI/CD pipeline:

1. **Unit Tests** - Fast tests (< 30 sec)
2. **Integration Tests** - Medium tests (< 5 min)
3. **Contract Tests** - API/gRPC contracts
4. **E2E Tests** - Full scenarios (< 15 min)

### Test Matrix
- **Python Versions**: 3.11+
- **Node.js Versions**: 18+
- **Browsers**: Chrome, Firefox, Safari
- **OS**: Ubuntu, macOS, Windows

## 📝 Writing New Tests

### Unit Test Template
```python
import pytest
from app.models.user import User

class TestUser:
    def test_user_creation(self, sample_user_data):
        user = User(**sample_user_data)
        assert user.username == sample_user_data["username"]
    
    def test_user_validation(self):
        with pytest.raises(ValueError):
            User(username="")
```

### Integration Test Template
```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.api
async def test_user_api_creation(async_client: AsyncClient):
    response = await async_client.post("/api/users", json={
        "username": "testuser",
        "email": "test@example.com"
    })
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"
```

### E2E Test Template
```typescript
import { test, expect } from '@playwright/test';

test('user login flow', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[data-testid="username"]', 'admin');
  await page.fill('[data-testid="password"]', 'password');
  await page.click('[data-testid="login-button"]');
  
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('[data-testid="welcome"]')).toBeVisible();
});
```

## 🆘 Troubleshooting

### Common Issues

1. **Database not available**
   ```bash
   # Check database connection
   pytest test/integration/database/ -v
   ```

2. **gRPC server not running**
   ```bash
   # Run gRPC tests
   pytest -m requires_grpc -v
   ```

3. **Frontend server unavailable**
   ```bash
   # Check port 3000 availability
   curl http://localhost:3000
   ```

### Test Logs
- **Pytest logs**: `test/logs/pytest.log`
- **Playwright logs**: `test-results/`
- **Coverage reports**: `htmlcov/`

## 📚 Documentation

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [Vitest Documentation](https://vitest.dev/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

## 🤝 Contributing

1. Add appropriate markers to new tests
2. Maintain code coverage at 80%+
3. Use existing fixtures where possible
4. Document complex test scenarios
5. Ensure tests pass locally before push

---

💡 **Tip**: Use `pytest --collect-only` to view all available tests without running them.
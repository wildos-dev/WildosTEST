# WildOS VPN Testing Infrastructure

This directory contains the complete testing infrastructure for the WildOS VPN project, which consists of three main components:

1. **FastAPI Backend** (`app/`) - Python API server
2. **WildosNode** (`wildosnode/`) - Python gRPC service 
3. **Dashboard** (`dashboard/`) - React/TypeScript frontend

## Directory Structure

```
test/
├── unit/                   # Unit tests
│   ├── app/               # FastAPI unit tests
│   ├── wildosnode/        # gRPC service unit tests
│   ├── dashboard/         # Frontend unit tests
│   └── conftest.py        # Unit test fixtures
├── integration/           # Integration tests
│   ├── grpc/              # gRPC integration tests
│   ├── api/               # API integration tests
│   ├── database/          # Database integration tests
│   └── conftest.py        # Integration test fixtures
├── contract/              # Contract tests (API/gRPC contracts)
│   ├── grpc/              # gRPC contract tests
│   ├── api/               # API contract tests
│   └── conftest.py        # Contract test fixtures
├── e2e/                   # End-to-end tests
│   ├── backend/           # Backend e2e tests
│   ├── frontend/          # Frontend e2e tests
│   ├── full_stack/        # Full stack e2e tests
│   └── conftest.py        # E2E test fixtures
├── fixtures/              # Test data and fixtures
│   ├── data/              # Test data files
│   ├── users/             # User fixtures
│   ├── nodes/             # Node fixtures
│   ├── configs/           # Configuration fixtures
│   ├── grpc_fixtures.py   # gRPC-specific fixtures
│   └── data_fixtures.py   # General data fixtures
├── config/                # Test configurations
│   ├── pytest.ini         # Main pytest config
│   ├── pytest_unit.ini    # Unit test config
│   ├── pytest_integration.ini # Integration test config
│   ├── pytest_e2e.ini     # E2E test config
│   ├── vitest.config.ts    # Vitest config for frontend
│   ├── playwright.config.ts # Playwright config for e2e
│   └── jest.config.js      # Jest config (alternative to vitest)
├── conftest.py            # Global test configuration
├── utils.py               # Testing utility functions
└── README.md              # This file
```

## Running Tests

### Python Tests (FastAPI + WildosNode)

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run specific test types
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m contract          # Contract tests only
pytest -m e2e               # E2E tests only

# Run tests with coverage
pytest --cov=app --cov=wildosnode --cov-report=html

# Run tests for specific component
pytest test/unit/app/        # FastAPI unit tests
pytest test/unit/wildosnode/ # WildosNode unit tests

# Run with specific configuration
pytest -c test/config/pytest_unit.ini
```

### Frontend Tests (Dashboard)

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
npm install

# Run vitest (preferred)
npm run test              # Run tests once
npm run test:watch        # Run tests in watch mode
npm run test:coverage     # Run with coverage
npm run test:ui           # Run with UI

# Run jest (alternative)
jest --config=../test/config/jest.config.js

# Run e2e tests with Playwright
npx playwright test --config=../test/config/playwright.config.ts
```

### Full Stack E2E Tests

```bash
# Run complete e2e test suite
pytest test/e2e/ -c test/config/pytest_e2e.ini

# Run with Playwright for browser tests
npx playwright test --config=test/config/playwright.config.ts
```

## Test Types Explained

### Unit Tests
- Test individual functions and classes in isolation
- Use mocks for external dependencies
- Fast execution, no external services required

### Integration Tests  
- Test interaction between components
- May use real database, gRPC connections
- Test API endpoints with real FastAPI app

### Contract Tests
- Verify API and gRPC contracts
- Ensure frontend and backend agree on interfaces
- Use Pact or custom schema validation

### End-to-End Tests
- Test complete user workflows
- Use real browser automation (Playwright)
- Test full application stack integration

## Test Markers

The following pytest markers are available:

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

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock
from app.models.user import User

@pytest.mark.unit
async def test_create_user(mock_database):
    # Test user creation logic
    user_data = {"username": "test", "email": "test@example.com"}
    user = await User.create(user_data, db=mock_database)
    assert user.username == "test"
```

### Integration Test Example

```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.api
async def test_user_api_endpoint(async_client: AsyncClient):
    response = await async_client.post("/api/users", json={
        "username": "test",
        "email": "test@example.com"
    })
    assert response.status_code == 201
    assert response.json()["username"] == "test"
```

### gRPC Test Example

```python
import pytest
from test.fixtures.grpc_fixtures import mock_grpc_client

@pytest.mark.grpc
@pytest.mark.integration
async def test_grpc_sync_users(mock_grpc_client, mock_user_data):
    await mock_grpc_client.sync_users(mock_user_data)
    mock_grpc_client.stub.SyncUsers.assert_called_once()
```

### Frontend Test Example

```typescript
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import UserList from '@/components/UserList'

describe('UserList', () => {
  it('renders user list correctly', () => {
    const users = [{ id: 1, username: 'test', email: 'test@example.com' }]
    render(<UserList users={users} />)
    expect(screen.getByText('test')).toBeInTheDocument()
  })
})
```

## Configuration

### Environment Variables for Testing

```bash
TESTING=1
DATABASE_URL=sqlite:///:memory:
SECRET_KEY=test-secret-key
JWT_SECRET_KEY=test-jwt-secret
DEBUG=False
```

### Test Database

Tests use SQLite in-memory database by default. For integration tests that need persistent data, you can configure PostgreSQL test database:

```bash
DATABASE_URL=postgresql://test:test@localhost:5432/wildosvpn_test
```

## CI/CD Integration

The testing infrastructure is designed to work with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Python Tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=app --cov=wildosnode --cov-report=xml

- name: Run Frontend Tests  
  run: |
    cd dashboard
    npm ci
    npm run test:coverage

- name: Run E2E Tests
  run: |
    npx playwright install
    npx playwright test
```

## Coverage Reports

Test coverage reports are generated in:
- `test/htmlcov/` - HTML coverage report for Python
- `test/coverage/` - Coverage report for frontend
- `test/playwright-report/` - Playwright test results

## Performance Testing

For performance testing, use:

```bash
# Benchmark tests
pytest --benchmark-only

# Load testing with locust
locust -f test/performance/locustfile.py
```

## Troubleshooting

### Common Issues

1. **gRPC Connection Errors**: Ensure WildosNode service is running for integration tests
2. **Database Errors**: Check database connection and permissions
3. **Frontend Test Failures**: Verify Node.js version compatibility
4. **E2E Test Timeouts**: Increase timeout values in playwright.config.ts

### Debug Mode

Run tests with verbose output:

```bash
pytest -v -s  # Python tests with output
npm run test -- --reporter=verbose  # Frontend tests
```

## Contributing

When adding new tests:

1. Follow the existing directory structure
2. Use appropriate test markers
3. Add fixtures to conftest.py files
4. Update this README if adding new test types
5. Ensure tests pass in CI/CD pipeline
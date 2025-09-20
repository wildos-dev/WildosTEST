"""
End-to-end test configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from playwright.async_api import async_playwright, Browser, Page


@pytest.fixture(scope="session")
async def browser() -> AsyncGenerator[Browser, None]:
    """Browser instance for e2e tests"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser: Browser) -> AsyncGenerator[Page, None]:
    """Page instance for e2e tests"""
    page = await browser.new_page()
    
    # Set viewport size
    await page.set_viewport_size({"width": 1280, "height": 720})
    
    # Set default timeout
    page.set_default_timeout(30000)
    
    yield page
    await page.close()


@pytest.fixture
def test_urls():
    """Test URLs for different environments"""
    return {
        "development": "http://localhost:3000",
        "staging": "https://staging.wildosvpn.com",
        "local_api": "http://localhost:8000/api"
    }


@pytest.fixture
def test_user_credentials():
    """Test user credentials for e2e tests"""
    return {
        "admin": {
            "username": "admin",
            "password": "admin123",
            "token": "test-admin-token"
        },
        "user": {
            "username": "testuser",
            "password": "user123", 
            "token": "test-user-token"
        }
    }


@pytest.fixture
async def authenticated_page(page: Page, test_urls, test_user_credentials):
    """Page with authenticated admin user"""
    # Navigate to login page
    await page.goto(f"{test_urls['development']}/login")
    
    # Login as admin
    await page.fill('[data-testid="input-username"]', test_user_credentials["admin"]["username"])
    await page.fill('[data-testid="input-password"]', test_user_credentials["admin"]["password"])
    await page.click('[data-testid="button-login"]')
    
    # Wait for dashboard to load
    await page.wait_for_url(f"{test_urls['development']}/dashboard")
    
    return page


@pytest.fixture
def e2e_test_data():
    """Test data for e2e scenarios"""
    return {
        "new_user": {
            "username": "e2e_testuser",
            "email": "e2e@test.com",
            "data_limit": "10",
            "expire_days": "30"
        },
        "new_node": {
            "name": "e2e-test-node",
            "address": "127.0.0.1",
            "port": "8080",
            "api_port": "8081"
        },
        "new_service": {
            "name": "e2e-test-service",
            "inbounds": ["vmess", "vless"]
        }
    }


@pytest.fixture
async def full_stack_setup():
    """Setup full application stack for e2e tests"""
    # This would start the full application stack
    # In a real implementation, this might use docker-compose
    # or other orchestration tools
    
    processes = {
        "backend": None,  # Start FastAPI backend
        "frontend": None,  # Start React frontend  
        "grpc": None,     # Start gRPC service
        "database": None  # Start test database
    }
    
    # Mock process startup
    yield processes
    
    # Cleanup
    for process_name, process in processes.items():
        if process:
            # Stop process
            pass
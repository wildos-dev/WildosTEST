"""
Изолированный conftest.py без проблемных импортов
"""
import os
import pytest

# Установка тестовых переменных окружения
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

@pytest.fixture
def sample_user():
    """Простая фикстура пользователя"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True
    }

@pytest.fixture
def sample_config():
    """Простая фикстура конфигурации"""
    return {
        "debug": True,
        "version": "1.0.0",
        "database_url": "sqlite:///:memory:"
    }
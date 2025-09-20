"""
Простые изолированные тесты для демонстрации системы тестирования
"""
import pytest
import asyncio
from datetime import datetime
import json


class TestBasicFunctionality:
    """Тесты базовой функциональности"""
    
    def test_datetime_operations(self):
        """Тест операций с датой и временем"""
        now = datetime.now()
        assert isinstance(now, datetime)
        assert now.year >= 2024
    
    def test_json_operations(self):
        """Тест операций с JSON"""
        data = {"test": "value", "number": 42}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed == data
    
    def test_list_operations(self):
        """Тест операций со списками"""
        test_list = [1, 2, 3, 4, 5]
        assert len(test_list) == 5
        assert sum(test_list) == 15
        assert max(test_list) == 5
    
    def test_dict_operations(self):
        """Тест операций со словарями"""
        test_dict = {"a": 1, "b": 2, "c": 3}
        assert "a" in test_dict
        assert test_dict["b"] == 2
        assert len(test_dict.keys()) == 3


class TestAsyncFunctionality:
    """Тесты асинхронной функциональности"""
    
    @pytest.mark.asyncio
    async def test_async_basic(self):
        """Базовый асинхронный тест"""
        async def async_func():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await async_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_async_gather(self):
        """Тест async gather"""
        async def async_task(value):
            await asyncio.sleep(0.05)
            return value * 2
        
        tasks = [async_task(i) for i in range(1, 4)]
        results = await asyncio.gather(*tasks)
        assert results == [2, 4, 6]


class TestMockingExamples:
    """Примеры тестов с мокированием"""
    
    def test_mock_basic(self):
        """Базовое мокирование"""
        from unittest.mock import Mock, MagicMock
        
        mock_obj = Mock()
        mock_obj.method.return_value = "mocked_result"
        
        result = mock_obj.method()
        assert result == "mocked_result"
        mock_obj.method.assert_called_once()
    
    def test_mock_async(self):
        """Мокирование асинхронных функций"""
        from unittest.mock import AsyncMock
        
        mock_async = AsyncMock()
        mock_async.return_value = "async_result"
        
        # Проверяем что это действительно AsyncMock
        assert isinstance(mock_async, AsyncMock)


@pytest.mark.integration
class TestIntegrationExamples:
    """Примеры интеграционных тестов"""
    
    def test_file_operations(self, tmp_path):
        """Тест операций с файлами"""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        
        # Запись в файл
        test_file.write_text(test_content)
        
        # Чтение из файла
        content = test_file.read_text()
        assert content == test_content
    
    def test_environment_variables(self, monkeypatch):
        """Тест переменных окружения"""
        monkeypatch.setenv("TEST_VAR", "test_value")
        
        import os
        assert os.getenv("TEST_VAR") == "test_value"


@pytest.mark.parametrize("input_val,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (5, 10),
])
def test_parametrized(input_val, expected):
    """Параметризованный тест"""
    assert input_val * 2 == expected


@pytest.mark.slow
def test_slow_operation():
    """Медленный тест (помечен как slow)"""
    import time
    time.sleep(0.1)
    assert True


@pytest.mark.unit
def test_unit_marker():
    """Тест с маркером unit"""
    assert 1 + 1 == 2


@pytest.mark.api
def test_api_marker():
    """Тест с маркером api"""
    # Симуляция API ответа
    api_response = {"status": "success", "data": {"id": 1}}
    assert api_response["status"] == "success"


class TestFixtureUsage:
    """Тесты использования фикстур"""
    
    @pytest.fixture
    def sample_data(self):
        """Локальная фикстура с тестовыми данными"""
        return {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "settings": {
                "debug": True,
                "version": "1.0.0"
            }
        }
    
    def test_fixture_usage(self, sample_data):
        """Тест использования фикстуры"""
        assert len(sample_data["users"]) == 2
        assert sample_data["settings"]["debug"] is True
        assert sample_data["settings"]["version"] == "1.0.0"
    
    def test_fixture_modification(self, sample_data):
        """Тест модификации данных фикстуры"""
        # Модифицируем данные
        sample_data["users"].append({"id": 3, "name": "Charlie"})
        
        assert len(sample_data["users"]) == 3
        assert sample_data["users"][-1]["name"] == "Charlie"


def test_exception_handling():
    """Тест обработки исключений"""
    with pytest.raises(ValueError):
        raise ValueError("Test exception")
    
    with pytest.raises(ZeroDivisionError):
        1 / 0


def test_approximate_values():
    """Тест приблизительных значений"""
    import math
    
    # Тест с приблизительным равенством
    assert math.pi == pytest.approx(3.14159, rel=1e-5)
    assert 0.1 + 0.2 == pytest.approx(0.3)


if __name__ == "__main__":
    # Запуск тестов напрямую
    pytest.main([__file__, "-v"])
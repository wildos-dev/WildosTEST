# Система тестирования WildOS VPN

Комплексная система тестирования для платформы WildOS VPN, обеспечивающая надёжность и качество всех компонентов системы.

## 🏗️ Архитектура тестирования

Система использует многоуровневую архитектуру тестирования:

### 📋 Типы тестов

- **Unit Tests** (`unit/`) - Модульные тесты для изолированного тестирования отдельных компонентов
- **Integration Tests** (`integration/`) - Интеграционные тесты для проверки взаимодействия между компонентами
- **Contract Tests** (`contract/`) - Контрактные тесты для API и gRPC интерфейсов
- **E2E Tests** (`e2e/`) - End-to-end тесты для полного пользовательского сценария
- **Functional Tests** (`functional/`) - Функциональные тесты для проверки бизнес-логики

### 🔧 Используемые инструменты

#### Backend тестирование (Python)
- **pytest** - Основной фреймворк тестирования
- **pytest-asyncio** - Поддержка асинхронного тестирования
- **httpx** - HTTP клиент для API тестов
- **unittest.mock** - Мокирование зависимостей

#### Frontend тестирование (TypeScript/JavaScript)
- **Vitest** - Быстрый unit тест раннер для Vue/React
- **Playwright** - E2E тестирование в браузерах
- **Jest** - Альтернативный фреймворк тестирования (legacy)

#### Инструменты покрытия кода
- **coverage.py** - Анализ покрытия Python кода
- **Istanbul** - Анализ покрытия JavaScript/TypeScript кода

## 📁 Структура проекта

```
test/
├── config/           # Конфигурационные файлы
│   ├── pytest.ini          # Конфигурация pytest
│   ├── jest.config.js       # Конфигурация Jest
│   ├── playwright.config.ts # Конфигурация Playwright
│   ├── vitest.config.ts     # Конфигурация Vitest
│   ├── global-setup.ts      # Глобальная настройка тестов
│   └── global-teardown.ts   # Глобальная очистка тестов
├── fixtures/         # Тестовые данные и фикстуры
│   ├── data_fixtures.py     # Фикстуры с тестовыми данными
│   ├── grpc_fixtures.py     # gRPC специфичные фикстуры
│   ├── configs/             # Тестовые конфигурации
│   ├── data/                # Тестовые данные
│   ├── nodes/               # Данные узлов для тестов
│   └── users/               # Пользовательские данные
├── unit/             # Модульные тесты
│   ├── app/                 # Тесты основного приложения
│   ├── dashboard/           # Тесты панели управления
│   └── wildosnode/          # Тесты узла WildOS
├── integration/      # Интеграционные тесты
│   ├── api/                 # Тесты API интеграции
│   ├── database/            # Тесты базы данных
│   ├── grpc/                # Тесты gRPC интеграции
│   └── middleware/          # Тесты middleware
├── contract/         # Контрактные тесты
│   ├── api/                 # API контракты
│   └── grpc/                # gRPC контракты
├── e2e/              # End-to-end тесты
│   ├── backend/             # Backend E2E тесты
│   ├── frontend/            # Frontend E2E тесты
│   └── full_stack/          # Полностековые E2E тесты
├── functional/       # Функциональные тесты
│   └── e2e/                 # Функциональные E2E тесты
├── conftest.py       # Глобальные pytest фикстуры
├── pytest.ini       # Основная конфигурация pytest
└── utils.py          # Утилиты для тестирования
```

## 🚀 Запуск тестов

### Все тесты
```bash
# Запуск всех тестов
pytest

# Запуск с подробным выводом
pytest -v

# Запуск с покрытием кода
pytest --cov=app --cov-report=html
```

### Модульные тесты
```bash
# Все unit тесты
pytest test/unit/

# Конкретный модуль
pytest test/unit/app/test_models/

# Конкретный тест
pytest test/unit/app/test_models/test_user_model.py::test_user_creation
```

### Интеграционные тесты
```bash
# Все integration тесты
pytest test/integration/

# API тесты
pytest test/integration/api/

# gRPC тесты
pytest test/integration/grpc/
```

### E2E тесты
```bash
# Playwright тесты
npx playwright test

# Запуск в конкретном браузере
npx playwright test --project=chromium

# Запуск с интерфейсом
npx playwright test --ui
```

### Frontend unit тесты
```bash
# Vitest тесты
npm run test

# Jest тесты (legacy)
npm run test:jest

# Тесты с покрытием
npm run test:coverage
```

## 🏷️ Маркеры тестов

Система использует pytest маркеры для категоризации тестов:

- `@pytest.mark.unit` - Модульные тесты
- `@pytest.mark.integration` - Интеграционные тесты
- `@pytest.mark.contract` - Контрактные тесты
- `@pytest.mark.e2e` - End-to-end тесты
- `@pytest.mark.grpc` - gRPC связанные тесты
- `@pytest.mark.api` - API тесты
- `@pytest.mark.database` - Тесты базы данных
- `@pytest.mark.slow` - Медленные тесты
- `@pytest.mark.requires_db` - Тесты, требующие базу данных
- `@pytest.mark.requires_grpc` - Тесты, требующие gRPC сервер

### Запуск по маркерам
```bash
# Только unit тесты
pytest -m unit

# Только интеграционные тесты
pytest -m integration

# Исключить медленные тесты
pytest -m "not slow"

# Комбинация маркеров
pytest -m "api and not slow"
```

## 🔧 Конфигурация

### Переменные окружения для тестов
```bash
TESTING=1
DATABASE_URL=sqlite:///:memory:
SECRET_KEY=test-secret-key-for-testing-only
JWT_SECRET_KEY=test-jwt-secret-key-for-testing-only
DEBUG=False
DOCS=False
```

### Порты тестирования
- Backend API: `8000`
- Frontend Dev Server: `3000`
- gRPC Server: `8080`

## 📊 Покрытие кода

Система требует минимум 80% покрытия кода:

```bash
# Генерация отчёта покрытия
pytest --cov=app --cov-report=html

# Просмотр HTML отчёта
open htmlcov/index.html
```

### Цели покрытия
- **Общее покрытие**: 80%
- **Ветки кода**: 80%
- **Функции**: 80%
- **Строки**: 80%

## 🔬 Фикстуры и тестовые данные

### Основные фикстуры
- `sample_user_data` - Данные пользователя
- `sample_admin_data` - Данные администратора
- `sample_node_data` - Данные узла
- `sample_service_data` - Данные сервиса
- `mock_logger` - Мок логгер
- `mock_redis` - Мок Redis клиент
- `async_client` - Асинхронный HTTP клиент

### Использование фикстур
```python
def test_user_creation(sample_user_data):
    user = User(**sample_user_data)
    assert user.username == "testuser"
    assert user.is_active is True
```

## 🐛 Отладка тестов

### Запуск с отладкой
```bash
# Остановка на первой ошибке
pytest -x

# Подробный вывод ошибок
pytest --tb=long

# Запуск конкретного теста с отладкой
pytest -s test/unit/app/test_models/test_user_model.py::test_user_creation
```

### Логирование в тестах
```python
import logging
logger = logging.getLogger(__name__)

def test_something():
    logger.info("Тест начался")
    # тестовый код
    logger.info("Тест завершён")
```

## 📈 CI/CD Integration

Тесты интегрированы в CI/CD пайплайн:

1. **Unit Tests** - Быстрые тесты (< 30 сек)
2. **Integration Tests** - Средние тесты (< 5 мин)
3. **Contract Tests** - API/gRPC контракты
4. **E2E Tests** - Полные сценарии (< 15 мин)

### Матрица тестирования
- **Python версии**: 3.11+
- **Node.js версии**: 18+
- **Браузеры**: Chrome, Firefox, Safari
- **ОС**: Ubuntu, macOS, Windows

## 📝 Создание новых тестов

### Unit тест шаблон
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

### Integration тест шаблон
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

### E2E тест шаблон
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

## 🆘 Поиск и устранение неисправностей

### Частые проблемы

1. **База данных не доступна**
   ```bash
   # Проверить подключение к БД
   pytest test/integration/database/ -v
   ```

2. **gRPC сервер не запущен**
   ```bash
   # Запустить gRPC тесты
   pytest -m requires_grpc -v
   ```

3. **Frontend сервер недоступен**
   ```bash
   # Проверить доступность порта 3000
   curl http://localhost:3000
   ```

### Логи тестирования
- **Pytest логи**: `test/logs/pytest.log`
- **Playwright логи**: `test-results/`
- **Coverage отчёты**: `htmlcov/`

## 📚 Документация

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [Vitest Documentation](https://vitest.dev/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

## 🤝 Участие в разработке

1. Добавьте соответствующие маркеры к новым тестам
2. Поддерживайте покрытие кода на уровне 80%+
3. Используйте существующие фикстуры где возможно
4. Документируйте сложные тестовые сценарии
5. Проверьте, что тесты проходят локально перед push

---

💡 **Совет**: Используйте команду `pytest --collect-only` для просмотра всех доступных тестов без их запуска.
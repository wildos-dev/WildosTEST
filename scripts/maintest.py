#!/usr/bin/env python3
"""
WildosVPN Replit Launch Script
Запускает проект в среде Replit БЕЗ wildosnode для тестирования dashboard
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path

# Настройка окружения для Replit (БЕЗ wildosnode)
os.environ.setdefault("DEBUG", "false")  # Отключаем DEBUG чтобы статические файлы dashboard работали
os.environ.setdefault("DOCS", "true") 
os.environ.setdefault("SUDO_USERNAME", "admin")
os.environ.setdefault("SUDO_PASSWORD", "admin123")
os.environ.setdefault("DASHBOARD_PATH", "/dashboard/")
os.environ.setdefault("DISABLE_RECORDING_NODE_USAGE", "true")
os.environ.setdefault("SQLALCHEMY_DATABASE_URL", "sqlite:///db.sqlite3")
os.environ.setdefault("UVICORN_HOST", "0.0.0.0")
os.environ.setdefault("UVICORN_PORT", "5000")
os.environ.setdefault("HOME_PAGE_TEMPLATE", "dashboard/dist/index.html")

# Создаем временную директорию для SSL сертификатов
temp_dir = tempfile.mkdtemp()
ssl_dir = Path(temp_dir) / "ssl"
ssl_dir.mkdir(exist_ok=True)
os.environ["WILDOSVPN_SSL_DIR"] = str(ssl_dir)

def create_wildosnode_mocks():
    """Создает полные моки для wildosnode модулей"""
    print("🔧 Создание моков для wildosnode...")
    
    import sys
    import types
    
    # Мок базового класса WildosNodeBase
    class MockWildosNodeBase:
        def __init__(self, *args, **kwargs):
            print("🚫 Mock: WildosNodeBase инициализирован (отключен)")
    
    # Мок gRPC клиента
    class MockWildosNodeGRPCLIB:
        def __init__(self, *args, **kwargs):
            print("🚫 Mock: WildosNodeGRPCLIB инициализирован (отключен)")
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, *args):
            pass
        
        async def sync_users(self, *args, **kwargs):
            return {"status": "mocked"}
        
        async def get_user_stats(self, *args, **kwargs):
            return {"upload": 0, "download": 0}
        
        async def restart_backend(self, *args, **kwargs):
            return {"status": "mocked"}
    
    # Создаем полноценный мок для operations субмодуля
    mock_operations = types.ModuleType('app.wildosnode.operations')
    
    # Добавляем все необходимые функции в operations
    async def mock_update_user(*args, **kwargs):
        print("🚫 Mock: update_user вызван (отключен)")
        return None
    
    async def mock_add_node(*args, **kwargs):
        print("🚫 Mock: add_node вызван (отключен)")
        return None
        
    async def mock_remove_node(*args, **kwargs):
        print("🚫 Mock: remove_node вызван (отключен)")
        return None
    
    async def mock_sync_users(*args, **kwargs):
        print("🚫 Mock: sync_users вызван (отключен)")
        return None
    
    async def mock_restart_backend(*args, **kwargs):
        print("🚫 Mock: restart_backend вызван (отключен)")
        return None
    
    # Присваиваем функции к модулю operations
    mock_operations.update_user = mock_update_user
    mock_operations.add_node = mock_add_node
    mock_operations.remove_node = mock_remove_node
    mock_operations.sync_users = mock_sync_users
    mock_operations.restart_backend = mock_restart_backend
    
    # Создаем основной мок модуль для wildosnode
    mock_wildosnode = types.ModuleType('app.wildosnode')
    mock_wildosnode.operations = mock_operations
    mock_wildosnode.WildosNodeGRPCLIB = MockWildosNodeGRPCLIB
    mock_wildosnode.WildosNodeBase = MockWildosNodeBase
    
    # Добавляем пустой словарь nodes для scheduler
    mock_wildosnode.nodes = {}
    
    # Добавляем дополнительные атрибуты которые могут потребоваться
    mock_wildosnode.get_nodes = lambda: {}
    mock_wildosnode.get_node = lambda node_id: None
    
    # Мок для nodes_startup
    async def mock_nodes_startup():
        print("🚫 Mock: nodes_startup отключен для Replit")
        return None
    
    # Создаем мок модуль для tasks.nodes
    mock_nodes_tasks = types.ModuleType('app.tasks.nodes')
    mock_nodes_tasks.nodes_startup = mock_nodes_startup
    
    # Регистрируем моки в sys.modules (важный порядок!)
    sys.modules['app.wildosnode'] = mock_wildosnode
    sys.modules['app.wildosnode.operations'] = mock_operations
    sys.modules['app.tasks.nodes'] = mock_nodes_tasks
    
    print("✅ Wildosnode моки созданы")

def patch_templates_early():
    """Патчит templates перед импортом FastAPI приложения"""
    print("🔧 Ранний патч templates...")
    
    # Патч render_template функции
    import app.templates
    from fastapi.responses import HTMLResponse
    
    def mock_render_template(template_name, context=None):
        """Мок для render_template, возвращает HTML напрямую"""
        print(f"🚫 Mock render_template вызван для: {template_name}")
        
        # Если запрашивается главная страница dashboard
        if "dashboard" in template_name or "index.html" in template_name:
            possible_paths = [
                "dashboard/dist/index.html",
                "dashboard/index.html", 
                "dashboard/public/index.html"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            html_content = f.read()
                        print(f"✅ Загружен dashboard: {path}")
                        return HTMLResponse(content=html_content, status_code=200)
                    except Exception as e:
                        print(f"⚠️  Ошибка чтения {path}: {e}")
                        continue
        
        # Fallback HTML для любых шаблонов
        fallback_html = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WildosVPN - Replit Test Mode</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            background: rgba(255,255,255,0.1);
            padding: 40px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
            max-width: 600px;
        }
        h1 { 
            font-size: 2.5rem; 
            margin-bottom: 20px; 
            background: linear-gradient(45deg, #FFD700, #FFA500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status { 
            padding: 15px 25px; 
            background: rgba(0,255,0,0.2); 
            border-radius: 8px; 
            margin: 25px 0;
            border: 1px solid rgba(0,255,0,0.3);
        }
        .info { 
            margin: 15px 0; 
            opacity: 0.9;
            line-height: 1.6;
        }
        .warning {
            background: rgba(255,165,0,0.2);
            border: 1px solid rgba(255,165,0,0.3);
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .api-link {
            display: inline-block;
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin: 10px;
            transition: background 0.3s;
        }
        .api-link:hover {
            background: rgba(255,255,255,0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ WildosVPN</h1>
        <div class="status">✅ Сервер запущен в Replit Test Mode</div>
        
        <div class="warning">
            <strong>⚠️ Режим тестирования</strong><br>
            WildosNode отключен для тестирования в Replit
        </div>
        
        <div class="info">
            <strong>Доступные эндпоинты:</strong><br>
            <a href="/docs" class="api-link">📚 API Documentation</a>
            <a href="/api/auth/admin" class="api-link">🔐 Admin API</a>
        </div>
        
        <div class="info">
            Dashboard файлы не найдены.<br>
            Для полного функционала соберите frontend:
            <br><code>cd dashboard && npm run build</code>
        </div>
    </div>
</body>
</html>
        """
        print("📱 Показ fallback страницы")
        return HTMLResponse(content=fallback_html, status_code=200)
    
    # Заменяем оригинальную функцию render_template
    app.templates.render_template = mock_render_template
    
    print("✅ Templates пропатчены")

def patch_fastapi_app():
    """Патчит FastAPI приложение для работы без wildosnode"""
    print("🔧 Настройка FastAPI для Replit...")
    
    # Патч lifespan для отключения nodes_startup
    import app.wildosvpn as main_app
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def replit_lifespan(app):
        print("🚀 Запуск lifespan (без wildosnode)")
        # Initialize system monitoring
        main_app.setup_system_monitoring()
        
        # НЕ инициализируем ноды для Replit
        print("🚫 Пропуск nodes_startup для Replit")
        
        main_app.logger.info("Application startup completed for Replit (без wildosnode)")
        yield
        
        main_app.logger.info("Application shutting down")
        if hasattr(main_app, 'scheduler'):
            main_app.scheduler.shutdown()
    
    # Заменяем оригинальный lifespan
    main_app.app.router.lifespan_context = replit_lifespan
    
    print("✅ FastAPI настроен для Replit")

def ensure_static_files_mounted():
    """Принудительно монтирует статические файлы dashboard для Replit"""
    print("🔧 Принудительное монтирование статических файлов dashboard...")
    
    import app.wildosvpn as main_app
    from starlette.staticfiles import StaticFiles
    from app.config.env import DASHBOARD_PATH
    
    # Проверяем наличие файлов dashboard
    if os.path.exists("dashboard/dist"):
        print("📁 Найдена директория dashboard/dist")
        
        # Монтируем основные файлы dashboard
        try:
            main_app.app.mount(
                DASHBOARD_PATH,
                StaticFiles(directory="dashboard/dist", html=True),
                name="dashboard",
            )
            print(f"✅ Dashboard смонтирован по пути: {DASHBOARD_PATH}")
        except Exception as e:
            print(f"⚠️  Ошибка монтирования dashboard: {e}")
        
        # Монтируем статические файлы
        if os.path.exists("dashboard/dist/static"):
            try:
                main_app.app.mount(
                    "/static/",
                    StaticFiles(directory="dashboard/dist/static"),
                    name="static",
                )
                print("✅ Статические файлы смонтированы: /static/")
            except Exception as e:
                print(f"⚠️  Ошибка монтирования /static/: {e}")
        
        # Монтируем локализации
        if os.path.exists("dashboard/dist/locales"):
            try:
                main_app.app.mount(
                    "/locales/",
                    StaticFiles(directory="dashboard/dist/locales"),
                    name="locales",
                )
                print("✅ Локализация смонтирована: /locales/")
            except Exception as e:
                print(f"⚠️  Ошибка монтирования /locales/: {e}")
    else:
        print("❌ Директория dashboard/dist не найдена!")
    
    print("✅ Статические файлы настроены")

def setup_directories():
    """Создает необходимые директории"""
    dirs = ["data", "data/ssl", "logs", "certs"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Директории созданы")

def main():
    """Основная функция запуска для Replit"""
    print("🚀 Запуск WildosVPN в Replit Test Mode (БЕЗ wildosnode)")
    print("=" * 60)
    
    # Настройка директорий
    setup_directories()
    
    # Создание моков для wildosnode
    create_wildosnode_mocks()
    
    # Ранний патч templates (до импорта FastAPI)
    patch_templates_early()
    
    # Настройка FastAPI
    patch_fastapi_app()
    
    # Принудительное монтирование статических файлов dashboard
    ensure_static_files_mounted()
    
    # Запуск сервера
    print("🌐 Запуск FastAPI сервера на порту 5000...")
    print("📱 Dashboard будет доступен по адресу: http://localhost:5000")
    print("📚 API документация: http://localhost:5000/docs")
    print("=" * 60)
    
    try:
        from app.wildosvpn import main as app_main
        asyncio.run(app_main())
    except KeyboardInterrupt:
        print("\n👋 Остановка сервера...")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
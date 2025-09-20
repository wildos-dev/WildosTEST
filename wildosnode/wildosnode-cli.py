#!/usr/bin/env python3
"""
WildosNode CLI - Инструмент командной строки для управления нодой WildosVPN
Версия: 1.0.0
"""

import os
import sys
import subprocess
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
import shutil

# Конфигурация
NODE_DIR = "/var/lib/wildosnode"
COMPOSE_FILE = "/opt/wildosvpn/docker-compose.node.yml"
BACKUP_DIR = "/var/backups/wildosnode"
LOG_FILE = f"{NODE_DIR}/logs/wildosnode-cli.log"

class Colors:
    """ANSI цветовые коды"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def colored_print(text, color=Colors.WHITE):
    """Цветной вывод текста"""
    print(f"{color}{text}{Colors.END}")

def log_action(message):
    """Логирование действий"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    colored_print(f"[{timestamp}] {message}", Colors.BLUE)

def run_command(command, capture_output=True):
    """Выполнение команды с обработкой ошибок"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(command, shell=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def check_docker():
    """Проверка наличия Docker"""
    success, _, _ = run_command("docker --version")
    if not success:
        colored_print("❌ Docker не найден. Установите Docker для работы с нодой.", Colors.RED)
        sys.exit(1)

def get_container_status():
    """Получение статуса контейнера ноды"""
    success, output, _ = run_command("docker compose -f /opt/wildosvpn/docker-compose.node.yml ps --format json")
    if success and output.strip():
        try:
            containers = []
            for line in output.strip().split('\n'):
                if line.strip():
                    containers.append(json.loads(line))
            return containers
        except json.JSONDecodeError:
            return []
    return []

def start_node():
    """Запуск ноды"""
    colored_print("🚀 Запуск WildosNode...", Colors.CYAN)
    
    if not os.path.exists(COMPOSE_FILE):
        colored_print("❌ Docker Compose файл не найден. Выполните установку сначала.", Colors.RED)
        return False
    
    success, output, error = run_command(f"docker compose -f {COMPOSE_FILE} up -d")
    
    if success:
        colored_print("✅ WildosNode успешно запущен", Colors.GREEN)
        log_action("WildosNode запущен")
        return True
    else:
        colored_print(f"❌ Ошибка при запуске: {error}", Colors.RED)
        return False

def stop_node():
    """Остановка ноды"""
    colored_print("🛑 Остановка WildosNode...", Colors.CYAN)
    
    success, output, error = run_command(f"docker compose -f {COMPOSE_FILE} down")
    
    if success:
        colored_print("✅ WildosNode остановлен", Colors.GREEN)
        log_action("WildosNode остановлен")
        return True
    else:
        colored_print(f"❌ Ошибка при остановке: {error}", Colors.RED)
        return False

def restart_node():
    """Перезапуск ноды"""
    colored_print("🔄 Перезапуск WildosNode...", Colors.CYAN)
    
    success, output, error = run_command(f"docker compose -f {COMPOSE_FILE} restart")
    
    if success:
        colored_print("✅ WildosNode перезапущен", Colors.GREEN)
        log_action("WildosNode перезапущен")
        return True
    else:
        colored_print(f"❌ Ошибка при перезапуске: {error}", Colors.RED)
        return False

def show_status():
    """Показать статус ноды"""
    colored_print("📊 Статус WildosNode:", Colors.CYAN)
    print()
    
    containers = get_container_status()
    
    if not containers:
        colored_print("❌ Контейнеры ноды не найдены или не запущены", Colors.RED)
        return
    
    for container in containers:
        name = container.get('Name', 'unknown')
        state = container.get('State', 'unknown')
        status = container.get('Status', 'unknown')
        
        if state.lower() == 'running':
            colored_print(f"  ✅ {name}: {status}", Colors.GREEN)
        else:
            colored_print(f"  ❌ {name}: {status}", Colors.RED)
    
    # Проверка использования ресурсов
    print()
    colored_print("💾 Использование ресурсов:", Colors.CYAN)
    
    # Диск
    if os.path.exists(NODE_DIR):
        disk_usage = shutil.disk_usage(NODE_DIR)
        used_percent = (disk_usage.used / disk_usage.total) * 100
        
        if used_percent < 80:
            color = Colors.GREEN
            icon = "✅"
        elif used_percent < 90:
            color = Colors.YELLOW
            icon = "⚠️"
        else:
            color = Colors.RED
            icon = "❌"
        
        colored_print(f"  {icon} Диск: {used_percent:.1f}% использовано", color)
    
    # Проверка логов
    if os.path.exists(f"{NODE_DIR}/logs"):
        log_files = list(Path(f"{NODE_DIR}/logs").glob("*.log"))
        colored_print(f"  📄 Файлов логов: {len(log_files)}", Colors.WHITE)

def show_logs(follow=False, lines=50):
    """Показать логи ноды"""
    colored_print(f"📋 Логи WildosNode (последние {lines} строк):", Colors.CYAN)
    
    command = f"docker compose -f {COMPOSE_FILE} logs --tail {lines}"
    if follow:
        command += " -f"
        colored_print("Нажмите Ctrl+C для выхода", Colors.YELLOW)
    
    run_command(command, capture_output=False)

def create_backup():
    """Создание резервной копии ноды"""
    if not os.path.exists(NODE_DIR):
        colored_print("❌ Директория ноды не найдена", Colors.RED)
        return False
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    backup_name = f"wildosnode-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    backup_path = f"{BACKUP_DIR}/{backup_name}.tar.gz"
    
    colored_print(f"💾 Создание резервной копии: {backup_name}", Colors.CYAN)
    
    # Создаем архив
    success, output, error = run_command(f"tar -czf {backup_path} -C {NODE_DIR} .")
    
    if success:
        size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
        colored_print(f"✅ Резервная копия создана: {backup_path} ({size:.1f} MB)", Colors.GREEN)
        log_action(f"Создана резервная копия: {backup_name}")
        return True
    else:
        colored_print(f"❌ Ошибка создания резервной копии: {error}", Colors.RED)
        return False

def restore_backup(backup_file):
    """Восстановление из резервной копии"""
    if not os.path.exists(backup_file):
        colored_print(f"❌ Файл резервной копии не найден: {backup_file}", Colors.RED)
        return False
    
    colored_print(f"🔄 Восстановление из резервной копии: {backup_file}", Colors.CYAN)
    
    # Останавливаем ноду
    stop_node()
    
    # Очищаем директорию
    if os.path.exists(NODE_DIR):
        shutil.rmtree(NODE_DIR)
    
    os.makedirs(NODE_DIR, exist_ok=True)
    
    # Восстанавливаем из архива
    success, output, error = run_command(f"tar -xzf {backup_file} -C {NODE_DIR}")
    
    if success:
        # Устанавливаем права доступа
        run_command(f"chown -R 1000:1000 {NODE_DIR}")
        
        colored_print("✅ Резервная копия восстановлена", Colors.GREEN)
        log_action(f"Восстановлена резервная копия: {os.path.basename(backup_file)}")
        
        # Запускаем ноду
        start_node()
        return True
    else:
        colored_print(f"❌ Ошибка восстановления: {error}", Colors.RED)
        return False

def list_backups():
    """Список резервных копий"""
    if not os.path.exists(BACKUP_DIR):
        colored_print("📁 Резервные копии не найдены", Colors.YELLOW)
        return
    
    backups = list(Path(BACKUP_DIR).glob("wildosnode-backup-*.tar.gz"))
    
    if not backups:
        colored_print("📁 Резервные копии не найдены", Colors.YELLOW)
        return
    
    colored_print("📁 Доступные резервные копии:", Colors.CYAN)
    print()
    
    for backup in sorted(backups, reverse=True):
        size = backup.stat().st_size / (1024 * 1024)  # MB
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        colored_print(f"  📄 {backup.name} ({size:.1f} MB, {mtime.strftime('%Y-%m-%d %H:%M')})", Colors.WHITE)

def update_node():
    """Обновление ноды"""
    colored_print("📦 Обновление WildosNode...", Colors.CYAN)
    
    # Создаем резервную копию перед обновлением
    if not create_backup():
        colored_print("❌ Не удалось создать резервную копию. Обновление отменено.", Colors.RED)
        return False
    
    # Обновляем через главный скрипт
    success, output, error = run_command("bash /opt/wildosvpn/wildosvpn.sh --mode=update")
    
    if success:
        colored_print("✅ Обновление завершено", Colors.GREEN)
        log_action("WildosNode обновлен")
        return True
    else:
        colored_print(f"❌ Ошибка обновления: {error}", Colors.RED)
        return False

def regenerate_certificates():
    """Перегенерация SSL сертификатов"""
    colored_print("🔐 Перегенерация SSL сертификатов...", Colors.CYAN)
    
    success, output, error = run_command("bash /opt/wildosvpn/wildosvpn.sh --generate-certs")
    
    if success:
        colored_print("✅ SSL сертификаты перегенерированы", Colors.GREEN)
        log_action("SSL сертификаты перегенерированы")
        
        # Перезапускаем ноду для применения новых сертификатов
        restart_node()
        return True
    else:
        colored_print(f"❌ Ошибка генерации сертификатов: {error}", Colors.RED)
        return False

def cleanup_logs():
    """Очистка старых логов"""
    colored_print("🧹 Очистка старых логов...", Colors.CYAN)
    
    log_dir = f"{NODE_DIR}/logs"
    if not os.path.exists(log_dir):
        colored_print("📁 Директория логов не найдена", Colors.YELLOW)
        return
    
    # Удаляем логи старше 30 дней
    success, output, error = run_command(f"find {log_dir} -name '*.log' -mtime +30 -delete")
    
    if success:
        colored_print("✅ Старые логи очищены", Colors.GREEN)
        log_action("Очищены старые логи")
    else:
        colored_print(f"❌ Ошибка очистки логов: {error}", Colors.RED)

def show_config():
    """Показать конфигурацию ноды"""
    colored_print("⚙️ Конфигурация WildosNode:", Colors.CYAN)
    print()
    
    config_files = [
        ("Xray Config", f"{NODE_DIR}/xray_config.json"),
        ("Server Certificate", f"{NODE_DIR}/server.cert"),
        ("Client Certificate", f"{NODE_DIR}/client.pem"),
        ("Server Key", f"{NODE_DIR}/server.key")
    ]
    
    for name, path in config_files:
        if os.path.exists(path):
            size = os.path.getsize(path)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            colored_print(f"  ✅ {name}: {os.path.basename(path)} ({size} bytes, {mtime.strftime('%Y-%m-%d %H:%M')})", Colors.GREEN)
        else:
            colored_print(f"  ❌ {name}: файл не найден", Colors.RED)

def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(
        description="WildosNode CLI - Инструмент управления нодой WildosVPN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  wildosnode start                    # Запустить ноду
  wildosnode status                   # Показать статус
  wildosnode logs -f                  # Следить за логами
  wildosnode backup                   # Создать резервную копию
  wildosnode restore backup.tar.gz    # Восстановить из копии
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команды управления
    subparsers.add_parser('start', help='Запустить ноду')
    subparsers.add_parser('stop', help='Остановить ноду')
    subparsers.add_parser('restart', help='Перезапустить ноду')
    subparsers.add_parser('status', help='Показать статус ноды')
    
    # Логи
    logs_parser = subparsers.add_parser('logs', help='Показать логи')
    logs_parser.add_argument('-f', '--follow', action='store_true', help='Следить за логами в реальном времени')
    logs_parser.add_argument('-n', '--lines', type=int, default=50, help='Количество строк для показа (по умолчанию: 50)')
    
    # Резервное копирование
    subparsers.add_parser('backup', help='Создать резервную копию')
    restore_parser = subparsers.add_parser('restore', help='Восстановить из резервной копии')
    restore_parser.add_argument('backup_file', help='Путь к файлу резервной копии')
    subparsers.add_parser('list-backups', help='Список резервных копий')
    
    # Обслуживание
    subparsers.add_parser('update', help='Обновить ноду')
    subparsers.add_parser('cleanup', help='Очистить старые логи')
    subparsers.add_parser('regen-certs', help='Перегенерировать SSL сертификаты')
    subparsers.add_parser('config', help='Показать конфигурацию ноды')
    
    args = parser.parse_args()
    
    if not args.command:
        colored_print("🔧 WildosNode v1.0.0", Colors.BOLD + Colors.CYAN)
        print()
        parser.print_help()
        return
    
    # Проверяем наличие Docker для большинства команд
    if args.command not in ['list-backups', 'config']:
        check_docker()
    
    # Выполняем команды
    if args.command == 'start':
        start_node()
    elif args.command == 'stop':
        stop_node()
    elif args.command == 'restart':
        restart_node()
    elif args.command == 'status':
        show_status()
    elif args.command == 'logs':
        show_logs(follow=args.follow, lines=args.lines)
    elif args.command == 'backup':
        create_backup()
    elif args.command == 'restore':
        restore_backup(args.backup_file)
    elif args.command == 'list-backups':
        list_backups()
    elif args.command == 'update':
        update_node()
    elif args.command == 'cleanup':
        cleanup_logs()
    elif args.command == 'regen-certs':
        regenerate_certificates()
    elif args.command == 'config':
        show_config()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        colored_print("\n👋 Выход из программы", Colors.YELLOW)
        sys.exit(0)
    except Exception as e:
        colored_print(f"❌ Неожиданная ошибка: {e}", Colors.RED)
        sys.exit(1)
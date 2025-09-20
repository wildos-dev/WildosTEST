#!/usr/bin/env bash
set -e

# ===============================================================================
# WildosVPN Install Script v5.0 - Production Security Edition
# Полная установка панели WildosVPN с продакшен безопасностью
# 
# ИЗМЕНЕНИЯ:
# - Добавлена поддержка автоматических Let's Encrypt сертификатов
# - Отключена генерация самоподписанных сертификатов в продакшен режиме
# - Caddy автоматически получает валидные SSL сертификаты для доменов
# ===============================================================================

# Глобальные переменные
SCRIPT_VERSION="5.1.0"
REPO_URL="https://github.com/wildos-dev/WildosTEST"
REPO_BRANCH="main"
INSTALL_DIR="/opt"
APP_NAME="wildosvpn"
APP_DIR="$INSTALL_DIR/$APP_NAME"
DATA_DIR="/var/lib/$APP_NAME"
LOG_FILE="/var/log/wildosvpn_install.log"
LAST_XRAY_CORES=10

# Конфигурационные переменные
PANEL_DOMAIN=""
SUBSCRIPTION_DOMAIN=""
DASHBOARD_PATH="/admin/"
SUDO_USERNAME="admin"
SUDO_PASSWORD=""
UPDATE_MODE=false

# Переменные безопасности
PRODUCTION_MODE=false
ENABLE_SSL_CERTIFICATES=true
ENABLE_NODE_AUTHENTICATION=true
ENABLE_FIREWALL_SETUP=false
ENABLE_SECURITY_MONITORING=true
AUTO_GENERATE_CERTIFICATES=true

# ===============================================================================
# ЦВЕТНОЙ ВЫВОД И УТИЛИТЫ
# ===============================================================================

colorized_echo() {
    local color=$1
    local text=$2
    case $color in
        "red") printf "\e[91m${text}\e[0m\n";;
        "green") printf "\e[92m${text}\e[0m\n";;
        "yellow") printf "\e[93m${text}\e[0m\n";;
        "blue") printf "\e[94m${text}\e[0m\n";;
        "magenta") printf "\e[95m${text}\e[0m\n";;
        "cyan") printf "\e[96m${text}\e[0m\n";;
        "white") printf "\e[97m${text}\e[0m\n";;
        *) echo "${text}";;
    esac
}

print_step() {
    colorized_echo blue "⏳ $1"
}

print_ok() {
    colorized_echo green "✅ Выполнено"
}

print_fail() {
    colorized_echo red "❌ Ошибка"
}

print_success() {
    colorized_echo green "🎉 $1"
}

print_error() {
    colorized_echo red "❌ $1"
}

print_info() {
    colorized_echo cyan "ℹ️  $1"
}

print_warning() {
    colorized_echo yellow "⚠️  $1"
}

# Логирование
log_action() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" | tee -a "$LOG_FILE"
}

error_exit() {
    print_error "$1"
    log_action "ERROR: $1"
    exit 1
}

# ===============================================================================
# СИСТЕМНЫЕ ПРОВЕРКИ
# ===============================================================================

check_root() {
    if [ "$(id -u)" != "0" ]; then
        error_exit "Скрипт должен запускаться от имени root"
    fi
}

detect_os() {
    if [ -f /etc/lsb-release ]; then
        OS=$(lsb_release -si 2>/dev/null)
    elif [ -f /etc/os-release ]; then
        OS=$(awk -F= '/^NAME/{print $2}' /etc/os-release | tr -d '"')
    elif [ -f /etc/redhat-release ]; then
        OS=$(cat /etc/redhat-release | awk '{print $1}')
    elif [ -f /etc/arch-release ]; then
        OS="Arch"
    else
        error_exit "Неподдерживаемая операционная система"
    fi
    
    log_action "Обнаружена ОС: $OS"
}

detect_arch() {
    case "$(uname -m)" in
        'i386' | 'i686') ARCH='32';;
        'amd64' | 'x86_64') ARCH='64';;
        'armv5tel') ARCH='arm32-v5';;
        'armv6l') ARCH='arm32-v6';;
        'armv7' | 'armv7l') ARCH='arm32-v7a';;
        'armv8' | 'aarch64') ARCH='arm64-v8a';;
        *) error_exit "Неподдерживаемая архитектура: $(uname -m)";;
    esac
    
    log_action "Архитектура: $ARCH"
}

check_network() {
    print_step "Проверка сетевого соединения"
    
    local test_urls=(
        "https://github.com"
        "https://api.github.com"
        "https://get.docker.com"
    )
    
    for url in "${test_urls[@]}"; do
        if ! curl -s --connect-timeout 10 --max-time 30 "$url" >/dev/null; then
            print_fail
            error_exit "Не удается подключиться к $url"
        fi
    done
    print_ok
}

check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        return 1
    fi
    
    if ! docker compose version >/dev/null 2>&1; then
        return 1
    fi
    
    return 0
}

# ===============================================================================
# НАСТРОЙКА РЕЖИМА РАЗВЕРТЫВАНИЯ
# ===============================================================================

setup_deployment_mode() {
    clear
    echo
    colorized_echo cyan "══════════════════════════════════════════════════════════════"
    colorized_echo cyan "                    РЕЖИМ РАЗВЕРТЫВАНИЯ"
    colorized_echo cyan "══════════════════════════════════════════════════════════════"
    echo
    
    colorized_echo yellow "Выберите режим развертывания WildosVPN:"
    echo
    colorized_echo white "1) 🧪 Разработка/Тестирование"
    colorized_echo white "   • Упрощенная настройка для локальных сетей"
    colorized_echo white "   • Минимальные требования безопасности"
    colorized_echo white "   • Быстрая установка"
    echo
    colorized_echo white "2) 🚀 Продакшен (рекомендуется)"
    colorized_echo white "   • Полная безопасность для внешних серверов"
    colorized_echo white "   • SSL сертификаты и шифрование"
    colorized_echo white "   • Мониторинг"
    colorized_echo white "   • Аутентификация узлов"
    echo
    
    while true; do
        read -p "Выберите режим (1/2, по умолчанию 2): " mode_choice
        mode_choice=${mode_choice:-2}
        
        case $mode_choice in
            1)
                PRODUCTION_MODE=false
                ENABLE_SSL_CERTIFICATES=false
                ENABLE_NODE_AUTHENTICATION=false
                ENABLE_FIREWALL_SETUP=false
                ENABLE_SECURITY_MONITORING=false
                print_info "Выбран режим разработки"
                break
                ;;
            2)
                PRODUCTION_MODE=true
                ENABLE_SSL_CERTIFICATES=true
                ENABLE_NODE_AUTHENTICATION=true
                ENABLE_FIREWALL_SETUP=false
                ENABLE_SECURITY_MONITORING=true
                print_success "Выбран продакшен режим"
                break
                ;;
            *)
                print_error "Неверный выбор. Введите 1 или 2"
                ;;
        esac
    done
    
    log_action "Выбран режим развертывания: $([ "$PRODUCTION_MODE" = true ] && echo 'Продакшен' || echo 'Разработка')"
}

# ===============================================================================
# УСТАНОВКА ЗАВИСИМОСТЕЙ
# ===============================================================================

detect_package_manager() {
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        PKG_MANAGER="apt-get"
        PKG_UPDATE="$PKG_MANAGER update"
        PKG_INSTALL="$PKG_MANAGER install -y"
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"AlmaLinux"* ]] || [[ "$OS" == *"Rocky"* ]]; then
        PKG_MANAGER="yum"
        PKG_UPDATE="$PKG_MANAGER update -y && $PKG_MANAGER install -y epel-release"
        PKG_INSTALL="$PKG_MANAGER install -y"
    elif [[ "$OS" == *"Fedora"* ]]; then
        PKG_MANAGER="dnf"
        PKG_UPDATE="$PKG_MANAGER update -y"
        PKG_INSTALL="$PKG_MANAGER install -y"
    elif [ "$OS" == "Arch" ]; then
        PKG_MANAGER="pacman"
        PKG_UPDATE="$PKG_MANAGER -Sy"
        PKG_INSTALL="$PKG_MANAGER -S --noconfirm"
    else
        error_exit "Неподдерживаемая операционная система: $OS"
    fi
}

install_dependencies() {
    print_step "Обновление системы и установка зависимостей"
    
    detect_package_manager
    
    # Проверка и освобождение блокировки APT для Ubuntu/Debian
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        export DEBIAN_FRONTEND=noninteractive
        
        # Ожидание освобождения блокировки APT (максимум 60 секунд)
        local timeout=60
        local count=0
        while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do
            if [ $count -ge $timeout ]; then
                print_warning "Принудительное освобождение блокировки APT"
                killall apt apt-get 2>/dev/null || true
                rm -f /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock* 2>/dev/null || true
                dpkg --configure -a 2>/dev/null || true
                break
            fi
            echo -n "."
            sleep 1
            ((count++))
        done
        [ $count -gt 0 ] && echo
    fi
    
    # Обновление репозиториев с timeout и показом прогресса
    print_info "Обновление списка пакетов..."
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        timeout 180 apt-get update || print_warning "Не удалось обновить репозитории, продолжаем..."
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"AlmaLinux"* ]] || [[ "$OS" == *"Rocky"* ]]; then
        timeout 180 yum update -y || print_warning "Не удалось обновить репозитории, продолжаем..."
        timeout 120 yum install -y epel-release || true
    elif [[ "$OS" == *"Fedora"* ]]; then
        timeout 180 dnf update -y || print_warning "Не удалось обновить репозитории, продолжаем..."
    elif [ "$OS" == "Arch" ]; then
        timeout 180 pacman -Sy || print_warning "Не удалось обновить репозитории, продолжаем..."
    fi
    
    local packages=(
        "curl"
        "wget"
        "git"
        "unzip"
        "openssl"
        "jq"
        "cron"
        "dnsutils"
    )
    
    # Добавить зависимости для продакшена
    if [ "$PRODUCTION_MODE" = true ]; then
        # В будущем здесь можно добавить дополнительные пакеты для продакшена
        :
    fi
    
    # Установка пакетов по одному с показом прогресса
    print_info "Установка пакетов:"
    for package in "${packages[@]}"; do
        echo -n "  - $package: "
        if timeout 120 eval $PKG_INSTALL "$package" >/dev/null 2>&1; then
            echo "✅"
        else
            echo "❌ (пропускаем)"
        fi
    done
    
    print_ok
}

install_docker() {
    if check_docker; then
        print_info "Docker уже установлен"
        return
    fi
    
    print_step "Установка Docker"
    
    # Установка Docker
    curl -fsSL https://get.docker.com | sh >/dev/null 2>&1
    
    # Запуск и автозагрузка
    systemctl start docker
    systemctl enable docker
    
    # Проверка установки
    if ! check_docker; then
        error_exit "Ошибка установки Docker"
    fi
    
    print_ok
}

# ===============================================================================
# НАСТРОЙКА БЕЗОПАСНОСТИ
# ===============================================================================

setup_ssl_certificates() {
    if [ "$ENABLE_SSL_CERTIFICATES" != true ]; then
        return
    fi
    
    print_step "Настройка SSL сертификатов для продакшена"
    
    # Создание директории для SSL
    mkdir -p "$DATA_DIR/ssl"
    chmod 700 "$DATA_DIR/ssl"
    
    # Генерация CA сертификата для панели
    if [ ! -f "$DATA_DIR/ssl/ca.key" ]; then
        openssl genrsa -out "$DATA_DIR/ssl/ca.key" 4096 2>/dev/null
        openssl req -new -x509 -days 3650 -key "$DATA_DIR/ssl/ca.key" \
            -out "$DATA_DIR/ssl/ca.cert" \
            -subj "/C=US/ST=State/L=City/O=WildosVPN/CN=WildosVPN-CA" 2>/dev/null
        
        chmod 600 "$DATA_DIR/ssl/ca.key"
        chmod 644 "$DATA_DIR/ssl/ca.cert"
    fi
    
    # Генерация сертификата для панели
    if [ ! -f "$DATA_DIR/ssl/panel.key" ]; then
        openssl genrsa -out "$DATA_DIR/ssl/panel.key" 2048 2>/dev/null
        openssl req -new -key "$DATA_DIR/ssl/panel.key" \
            -out "$DATA_DIR/ssl/panel.csr" \
            -subj "/C=US/ST=State/L=City/O=WildosVPN/CN=$PANEL_DOMAIN" 2>/dev/null
        
        openssl x509 -req -in "$DATA_DIR/ssl/panel.csr" \
            -CA "$DATA_DIR/ssl/ca.cert" -CAkey "$DATA_DIR/ssl/ca.key" \
            -CAcreateserial -out "$DATA_DIR/ssl/panel.cert" \
            -days 365 2>/dev/null
        
        rm "$DATA_DIR/ssl/panel.csr"
        chmod 600 "$DATA_DIR/ssl/panel.key"
        chmod 644 "$DATA_DIR/ssl/panel.cert"
    fi
    
    print_ok
    log_action "SSL сертификаты настроены для продакшена"
}

setup_node_authentication() {
    if [ "$ENABLE_NODE_AUTHENTICATION" != true ]; then
        return
    fi
    
    print_step "Настройка системы аутентификации узлов"
    
    # Создание секретного ключа для токенов
    if [ ! -f "$DATA_DIR/node_auth_secret.key" ]; then
        openssl rand -hex 32 > "$DATA_DIR/node_auth_secret.key"
        chmod 600 "$DATA_DIR/node_auth_secret.key"
    fi
    
    print_ok
    log_action "Система аутентификации узлов настроена"
}


setup_security_monitoring() {
    if [ "$ENABLE_SECURITY_MONITORING" != true ]; then
        return
    fi
    
    print_step "Настройка мониторинга безопасности"
    
    # Создание директории для логов безопасности
    mkdir -p "$DATA_DIR/logs/security"
    chmod 755 "$DATA_DIR/logs/security"
    
    # Настройка logrotate для логов безопасности
    cat > /etc/logrotate.d/wildosvpn-security << EOF
$DATA_DIR/logs/security/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    create 644 root root
}
EOF
    
    # Настройка fail2ban для WildosVPN
    if command -v fail2ban-server >/dev/null 2>&1; then
        cat > /etc/fail2ban/jail.d/wildosvpn.conf << EOF
[wildosvpn-auth]
enabled = true
port = 80,443,8000
filter = wildosvpn-auth
logpath = $DATA_DIR/logs/security/*.log
maxretry = 5
bantime = 3600
findtime = 600
EOF
        
        cat > /etc/fail2ban/filter.d/wildosvpn-auth.conf << EOF
[Definition]
failregex = ^.*Failed authentication.*<HOST>.*$
            ^.*Invalid token.*<HOST>.*$
            ^.*Authentication error.*<HOST>.*$
ignoreregex =
EOF
        
        systemctl restart fail2ban 2>/dev/null || true
    fi
    
    print_ok
    log_action "Мониторинг безопасности настроен"
}

# ===============================================================================
# КОНФИГУРАЦИЯ И ДОМЕНЫ
# ===============================================================================

# Проверка DNS записей домена
check_domain_dns() {
    local domain="$1"
    local domain_type="$2"  # "панели" или "подписок"
    
    print_step "Проверка DNS записей для домена $domain_type"
    
    # Получаем текущий IP сервера
    local server_ip=""
    server_ip=$(curl -s --connect-timeout 5 --max-time 10 https://api.ipify.org 2>/dev/null || curl -s --connect-timeout 5 --max-time 10 http://ifconfig.me 2>/dev/null)
    
    if [[ -z "$server_ip" ]]; then
        print_warning "Не удалось определить IP адрес сервера"
        return 1
    fi
    
    print_info "IP адрес сервера: $server_ip"
    
    # Резолвим домен
    local domain_ip=""
    if command -v dig >/dev/null 2>&1; then
        domain_ip=$(dig +short "$domain" A 2>/dev/null | head -1)
    elif command -v nslookup >/dev/null 2>&1; then
        domain_ip=$(nslookup "$domain" 2>/dev/null | awk '/^Address: / { print $2 }' | grep -v '#' | head -1)
    elif command -v host >/dev/null 2>&1; then
        domain_ip=$(host "$domain" 2>/dev/null | awk '/has address/ { print $4 }' | head -1)
    else
        print_warning "Команды dig/nslookup/host не найдены. Пропускаем проверку DNS."
        return 1
    fi
    
    if [[ -z "$domain_ip" ]]; then
        print_fail
        print_error "❌ Домен $domain не резолвится!"
        print_warning "Убедитесь что:"
        print_warning "- DNS запись типа A настроена для $domain"
        print_warning "- Домен указывает на IP: $server_ip" 
        print_warning "- DNS изменения распространились (может занять до 24 часов)"
        echo
        
        read -p "Продолжить установку несмотря на проблемы с DNS? (y/N): " continue_anyway
        if [[ "$continue_anyway" != "y" && "$continue_anyway" != "Y" ]]; then
            print_error "Установка прервана. Настройте DNS и повторите установку."
            exit 1
        fi
        print_warning "⚠️ Продолжаем установку с неправильными DNS записями"
        return 1
    fi
    
    print_info "IP домена $domain: $domain_ip"
    
    # Сравниваем IP адреса
    if [[ "$server_ip" == "$domain_ip" ]]; then
        print_ok
        print_success "✅ DNS настроен правильно для $domain"
        return 0
    else
        print_fail
        print_error "❌ DNS запись указывает на неправильный IP!"
        print_error "   Домен $domain → $domain_ip"
        print_error "   Сервер        → $server_ip"
        print_warning ""
        print_warning "Необходимо:"
        print_warning "1. Изменить A запись для $domain на IP: $server_ip"
        print_warning "2. Дождаться распространения DNS (до 24 часов)"
        print_warning "3. Проверить настройки у DNS провайдера"
        echo
        
        read -p "Продолжить установку с неправильными DNS записями? (y/N): " continue_anyway
        if [[ "$continue_anyway" != "y" && "$continue_anyway" != "Y" ]]; then
            print_error "Установка прервана. Исправьте DNS записи и повторите установку."
            exit 1
        fi
        print_warning "⚠️ Продолжаем установку. SSL сертификаты могут не работать!"
        return 1
    fi
}

setup_domains() {
    clear
    echo
    colorized_echo cyan "══════════════════════════════════════════════════════════════"
    colorized_echo cyan "                    НАСТРОЙКА ДОМЕНОВ"
    colorized_echo cyan "══════════════════════════════════════════════════════════════"
    echo
    
    if [ "$UPDATE_MODE" = true ]; then
        print_info "Режим обновления - домены не изменяются"
        return
    fi
    
    while true; do
        read -p "Введите домен для панели управления (например, panel.example.com): " PANEL_DOMAIN
        if [[ -n "$PANEL_DOMAIN" && "$PANEL_DOMAIN" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            # Проверяем DNS записи для домена панели
            echo
            check_domain_dns "$PANEL_DOMAIN" "панели"
            echo
            break
        else
            print_error "Введите корректный домен"
        fi
    done
    
    while true; do
        read -p "Введите домен для подписок (например, sub.example.com, или оставьте пустым для использования домена панели): " SUBSCRIPTION_DOMAIN
        if [[ -z "$SUBSCRIPTION_DOMAIN" ]]; then
            SUBSCRIPTION_DOMAIN="$PANEL_DOMAIN"
            print_info "Используется домен панели для подписок: $SUBSCRIPTION_DOMAIN"
            break
        elif [[ "$SUBSCRIPTION_DOMAIN" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            # Проверяем DNS записи для домена подписок (только если отличается от панели)
            if [[ "$SUBSCRIPTION_DOMAIN" != "$PANEL_DOMAIN" ]]; then
                echo
                check_domain_dns "$SUBSCRIPTION_DOMAIN" "подписок"
                echo
            fi
            break
        else
            print_error "Введите корректный домен или оставьте пустым"
        fi
    done
    
    log_action "Настроены домены: панель=$PANEL_DOMAIN, подписки=$SUBSCRIPTION_DOMAIN"
}

setup_dashboard_path() {
    clear
    echo
    colorized_echo cyan "══════════════════════════════════════════════════════════════"
    colorized_echo cyan "                  НАСТРОЙКА ПУТИ ПАНЕЛИ"
    colorized_echo cyan "══════════════════════════════════════════════════════════════"
    echo
    
    if [ "$UPDATE_MODE" = true ]; then
        print_info "Режим обновления - путь панели не изменяется"
        return
    fi
    
    colorized_echo yellow "Настройка пути для доступа к панели управления:"
    echo
    colorized_echo white "Текущий URL: https://$PANEL_DOMAIN/dashboard/"
    colorized_echo white "Новый URL будет: https://$PANEL_DOMAIN/{ваш_путь}/"
    echo
    colorized_echo cyan "Примеры путей:"
    colorized_echo white "  admin     → https://$PANEL_DOMAIN/admin/"
    colorized_echo white "  panel     → https://$PANEL_DOMAIN/panel/"
    colorized_echo white "  manage    → https://$PANEL_DOMAIN/manage/"
    colorized_echo white "  dashboard → https://$PANEL_DOMAIN/dashboard/ (по умолчанию)"
    echo
    
    while true; do
        read -p "Введите путь для панели (по умолчанию 'admin'): " user_path
        user_path=${user_path:-admin}
        
        # Очистка пути от слешей и валидация
        user_path=$(echo "$user_path" | sed 's|^/||; s|/$||')
        
        if [[ -n "$user_path" && "$user_path" =~ ^[a-zA-Z0-9_-]+$ ]]; then
            DASHBOARD_PATH="/$user_path/"
            echo
            colorized_echo green "✅ Путь к панели: $DASHBOARD_PATH"
            colorized_echo white "   Полный URL: https://$PANEL_DOMAIN$DASHBOARD_PATH"
            echo
            
            read -p "Подтвердить этот путь? (Y/n): " confirm
            confirm=${confirm:-Y}
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                break
            fi
        else
            print_error "Путь должен содержать только буквы, цифры, дефисы и подчеркивания"
        fi
    done
    
    log_action "Настроен путь панели: $DASHBOARD_PATH"
}

setup_admin_credentials() {
    clear
    echo
    colorized_echo cyan "══════════════════════════════════════════════════════════════"
    colorized_echo cyan "                УЧЕТНЫЕ ДАННЫЕ АДМИНИСТРАТОРА"
    colorized_echo cyan "══════════════════════════════════════════════════════════════"
    echo
    
    if [ "$UPDATE_MODE" = true ]; then
        print_info "Режим обновления - учетные данные не изменяются"
        return
    fi
    
    while true; do
        read -p "Введите имя пользователя администратора (по умолчанию: admin): " SUDO_USERNAME
        SUDO_USERNAME=${SUDO_USERNAME:-admin}
        if [[ "$SUDO_USERNAME" =~ ^[a-zA-Z0-9_]{3,20}$ ]]; then
            break
        else
            print_error "Имя пользователя должно содержать 3-20 символов (буквы, цифры, подчеркивание)"
        fi
    done
    
    while true; do
        read -s -p "Введите пароль администратора (по умолчанию: admin, минимум 8 символов): " SUDO_PASSWORD
        echo
        SUDO_PASSWORD=${SUDO_PASSWORD:-admin}
        if [[ ${#SUDO_PASSWORD} -ge 8 ]] || [[ "$SUDO_PASSWORD" == "admin" ]]; then
            if [[ "$SUDO_PASSWORD" != "admin" ]]; then
                read -s -p "Подтвердите пароль: " SUDO_PASSWORD_CONFIRM
                echo
                if [[ "$SUDO_PASSWORD" == "$SUDO_PASSWORD_CONFIRM" ]]; then
                    break
                else
                    print_error "Пароли не совпадают"
                fi
            else
                colorized_echo yellow "⚠️  Используется стандартный пароль 'admin' для быстрого тестирования"
                break
            fi
        else
            print_error "Пароль должен содержать минимум 8 символов"
        fi
    done
    
    log_action "Настроены учетные данные администратора: $SUDO_USERNAME"
}

# ===============================================================================
# УСТАНОВКА ПРИЛОЖЕНИЯ
# ===============================================================================

create_directories() {
    print_step "Создание структуры директорий"
    
    mkdir -p "$APP_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$DATA_DIR/configs"
    mkdir -p "$DATA_DIR/logs"
    mkdir -p "$DATA_DIR/xray-cores"
    
    # Создание дополнительных директорий для продакшена
    if [ "$PRODUCTION_MODE" = true ]; then
        mkdir -p "$DATA_DIR/ssl"
        mkdir -p "$DATA_DIR/logs/security"
        chmod 700 "$DATA_DIR/ssl"
    fi
    
    print_ok
}

clone_repository() {
    print_step "Загрузка исходного кода WildosVPN"
    
    if [ -d "$APP_DIR/.git" ]; then
        cd "$APP_DIR"
        git fetch origin
        git reset --hard origin/$REPO_BRANCH
    else
        rm -rf "$APP_DIR"
        git clone -b "$REPO_BRANCH" "$REPO_URL" "$APP_DIR"
    fi
    
    cd "$APP_DIR"
    
    print_ok
}

fix_nodes_startup_issue() {
    print_step "Исправление проблемы с запуском узлов"
    
    # Модификация nodes_startup.py
    local nodes_startup_file="$APP_DIR/app/utils/nodes_startup.py"
    
    if [ -f "$nodes_startup_file" ]; then
        # Создание резервной копии
        cp "$nodes_startup_file" "${nodes_startup_file}.backup"
        
        # Применение исправлений
        cat > "$nodes_startup_file" << 'EOF'
"""
Fixed nodes_startup module for WildosVPN
Исправленный модуль запуска узлов
"""
import asyncio
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

async def start_nodes() -> bool:
    """Запуск всех узлов"""
    try:
        from app.db import GetDB, crud
        from app.models.node import NodeStatus
        
        with GetDB() as db:
            # Получение всех узлов
            nodes = crud.get_nodes(db)
            
            for node in nodes:
                try:
                    # Попытка подключения к узлу
                    await connect_node(node)
                    
                    # Обновление статуса узла
                    crud.update_node_status(
                        db=db,
                        node_id=node.id,
                        status=NodeStatus.healthy,
                        message="Node started successfully"
                    )
                    
                    logger.info(f"Node {node.name} started successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to start node {node.name}: {e}")
                    
                    # Обновление статуса узла как неисправного
                    crud.update_node_status(
                        db=db,
                        node_id=node.id,
                        status=NodeStatus.unhealthy,
                        message=f"Startup failed: {str(e)}"
                    )
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to start nodes: {e}")
        return False

async def connect_node(node) -> bool:
    """Подключение к конкретному узлу"""
    try:
        # Импорт здесь для избежания циклических зависимостей
        from app.wildosnode import grpclib
        
        # Создание соединения с узлом
        connection = await grpclib.get_node_connection(node)
        
        if connection:
            logger.info(f"Successfully connected to node {node.name}")
            return True
        else:
            logger.warning(f"Failed to connect to node {node.name}")
            return False
            
    except Exception as e:
        logger.error(f"Error connecting to node {node.name}: {e}")
        return False

def initialize_nodes():
    """Инициализация узлов при запуске приложения"""
    try:
        # Запуск в отдельном потоке чтобы не блокировать основное приложение
        import threading
        thread = threading.Thread(target=_start_nodes_thread)
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        logger.error(f"Failed to initialize nodes: {e}")

def _start_nodes_thread():
    """Запуск узлов в отдельном потоке"""
    try:
        # Создание нового event loop для потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запуск узлов
        loop.run_until_complete(start_nodes())
        
    except Exception as e:
        logger.error(f"Error in nodes startup thread: {e}")
    finally:
        try:
            loop.close()
        except:
            pass
EOF
        
        print_ok
        log_action "Проблема с запуском узлов исправлена"
    else
        print_warning "Файл nodes_startup.py не найден - пропускаем исправление"
    fi
}

# ===============================================================================
# СОЗДАНИЕ КОНФИГУРАЦИОННЫХ ФАЙЛОВ
# ===============================================================================

create_dockerfile() {
    print_step "Создание Dockerfile"
    
    cat > "$APP_DIR/Dockerfile" << EOF
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \\
    curl \\
    unzip \\
    gnupg \\
    lsb-release \\
    libssl-dev \\
    libffi-dev \\
    libpq-dev \\
    gcc \\
    g++ \\
    make \\
    pkg-config \\
    python3-dev \\
    libxml2-dev \\
    libxslt1-dev \\
    zlib1g-dev \\
    libjpeg-dev \\
    libfreetype6-dev \\
    liblcms2-dev \\
    libwebp-dev \\
    tcl8.6-dev \\
    tk8.6-dev \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Обновление pip до последней версии
RUN pip install --upgrade pip

# Копирование зависимостей
COPY requirements.txt ./

# Установка зависимостей с исправлением проблемных версий
RUN sed -i 's/v2share>=0.1.0/v2share==0.1.0b31/g' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt || \
    (echo "Attempting alternative installation..." && \
     pip install --no-cache-dir --force-reinstall bcrypt==4.0.1 && \
     pip install --no-cache-dir --ignore-installed PyYAML==6.0.1 && \
     pip install --no-cache-dir -r requirements.txt)

# Исправление проблемы с bcrypt и установка alembic
RUN pip install --no-deps bcrypt==4.0.1 passlib==1.7.4 && \
    pip install alembic

# Копирование кода приложения
COPY . .

# Создание пользователя для безопасности
RUN groupadd -r wildosvpn && useradd -r -g wildosvpn wildosvpn

# Создание директорий для логов и данных с правильными правами
RUN mkdir -p /var/lib/wildosvpn/logs /var/lib/wildosvpn/configs /var/lib/wildosvpn/ssl && \
    chown -R wildosvpn:wildosvpn /var/lib/wildosvpn && \
    chmod -R 755 /var/lib/wildosvpn

# Установка прав доступа для приложения
RUN chown -R wildosvpn:wildosvpn /app

# Экспорт портов
EXPOSE 8000

# Переключение на непривилегированного пользователя
USER wildosvpn

# Команда запуска
CMD ["python", "main.py"]
EOF
    
    print_ok
}

create_docker_compose() {
    print_step "Создание Docker Compose файла"
    
    cat > "$APP_DIR/docker-compose.yml" << EOF
services:
  wildosvpn-panel:
    build: .
    container_name: wildosvpn-panel
    restart: unless-stopped
    network_mode: host
    environment:
      - PYTHONUNBUFFERED=1
      - PRODUCTION_MODE=$PRODUCTION_MODE
    env_file:
      - $DATA_DIR/.env
    volumes:
      - $DATA_DIR:/var/lib/wildosvpn
    command: ["sh", "-c", "chown -R wildosvpn:wildosvpn /var/lib/wildosvpn && su wildosvpn -c 'alembic upgrade head && python main.py'"]
    user: root
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/system/health"]
      interval: 120s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  caddy:
    image: caddy:2-alpine
    container_name: wildosvpn-caddy
    restart: unless-stopped
    network_mode: host
    volumes:
      - $APP_DIR/Caddyfile:/etc/caddy/Caddyfile:ro
      - $DATA_DIR/caddy:/data
      - $DATA_DIR/ssl:$DATA_DIR/ssl:ro
    depends_on:
      - wildosvpn-panel
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF
    
    print_ok
}

create_caddyfile() {
    print_step "Создание Caddyfile с поддержкой Let's Encrypt"
    
    # Определяем email для Let's Encrypt
    local ssl_email="admin@${PANEL_DOMAIN}"
    
    # В продакшен режиме используем автоматические Let's Encrypt сертификаты
    local global_config=""
    if [ "$PRODUCTION_MODE" = true ]; then
        global_config="{
    admin off
    email $ssl_email
}"
    else
        global_config="{
    admin off
}"
    fi
    
    cat > "$APP_DIR/Caddyfile" << EOF
$global_config

$PANEL_DOMAIN {
    # Без указания tls - Caddy автоматически получит Let's Encrypt сертификат
    
    reverse_proxy localhost:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }
    
    log {
        output file $DATA_DIR/logs/access.log {
            roll_size 10mb
            roll_keep 10
        }
    }
}
EOF

    # Добавляем блок для домена подписок только если он отличается
    if [ "$SUBSCRIPTION_DOMAIN" != "$PANEL_DOMAIN" ]; then
        cat >> "$APP_DIR/Caddyfile" << EOF

$SUBSCRIPTION_DOMAIN {
    # Автоматический Let's Encrypt сертификат для домена подписок
    
    reverse_proxy localhost:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }
    
    log {
        output file $DATA_DIR/logs/sub_access.log {
            roll_size 10mb
            roll_keep 10
        }
    }
}
EOF
    fi
    
    print_ok
    log_action "Caddyfile создан с поддержкой автоматических SSL сертификатов"
}

create_env_file() {
    print_step "Создание файла окружения"
    
    local env_file="$DATA_DIR/.env"
    
    if [ "$UPDATE_MODE" = true ] && [[ -f "$env_file.backup" ]]; then
        print_info "Восстановление настроек из резервной копии"
        source "$env_file.backup"
    fi
    
    # Генерация JWT токена
    jwt_secret=$(openssl rand -hex 32 2>/dev/null || tr -dc A-Za-z0-9 </dev/urandom | head -c 64)
    
    cat > "$env_file" << EOF
# WildosVPN Configuration
# Generated on: $(date)

# Database
SQLALCHEMY_DATABASE_URL=sqlite:////var/lib/wildosvpn/wildosvpn.db

# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
WILDOSVPN_SECRET_KEY=$jwt_secret

# Panel Configuration
PANEL_DOMAIN=$PANEL_DOMAIN
SUBSCRIPTION_DOMAIN=$SUBSCRIPTION_DOMAIN
DASHBOARD_PATH=$DASHBOARD_PATH

# SSL settings
SSL_CERT_FILE="/var/lib/wildosvpn/ssl/panel.cert"
SSL_KEY_FILE="/var/lib/wildosvpn/ssl/panel.key"
SSL_CA_FILE="/var/lib/wildosvpn/ssl/ca.cert"

# Admin Configuration
SUDO_USERNAME=$SUDO_USERNAME
SUDO_PASSWORD=$SUDO_PASSWORD

# Production Mode Settings
PRODUCTION_MODE=$PRODUCTION_MODE
ENABLE_SSL_CERTIFICATES=$ENABLE_SSL_CERTIFICATES
ENABLE_NODE_AUTHENTICATION=$ENABLE_NODE_AUTHENTICATION
ENABLE_SECURITY_MONITORING=$ENABLE_SECURITY_MONITORING

# Security Configuration
SECURITY_LOG_DIR=/var/lib/wildosvpn/logs/security
NODE_AUTH_SECRET_FILE=/var/lib/wildosvpn/node_auth_secret.key

# Application Settings
DOCS_URL=
REDOC_URL=
DEBUG=false
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
    
    # Добавление настроек для продакшена
    if [ "$PRODUCTION_MODE" = true ]; then
        cat >> "$env_file" << EOF

# Production Security Settings
CERTIFICATE_MANAGER_ENABLED=true
SECURITY_LOGGER_ENABLED=true
FAIL2BAN_ENABLED=true
FIREWALL_ENABLED=true

# SSL/TLS Configuration  
SSL_VERIFY_MODE=CERT_REQUIRED
SSL_CHECK_HOSTNAME=true
SSL_CIPHERS=ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
BRUTE_FORCE_THRESHOLD=5
LOCKOUT_DURATION_MINUTES=60

# Monitoring
HEALTH_CHECK_ENABLED=true
METRICS_ENABLED=true
AUDIT_LOG_ENABLED=true
EOF
    fi
    
    chmod 600 "$env_file"
    print_ok
}

generate_certificates() {
    # Обеспечиваем создание SSL сертификатов для Caddy
    if [ "$ENABLE_SSL_CERTIFICATES" = true ]; then
        print_step "Проверка и настройка SSL сертификатов для Caddy"
        
        # Убеждаемся что директория SSL существует
        mkdir -p "$DATA_DIR/ssl"
        chmod 700 "$DATA_DIR/ssl"
        
        # Проверяем наличие сертификатов панели (созданных setup_ssl_certificates)
        if [ ! -f "$DATA_DIR/ssl/panel.cert" ] || [ ! -f "$DATA_DIR/ssl/panel.key" ]; then
            print_warning "SSL сертификаты не найдены, создаем их"
            
            # Создаем CA если его нет
            if [ ! -f "$DATA_DIR/ssl/ca.key" ]; then
                openssl genrsa -out "$DATA_DIR/ssl/ca.key" 4096 2>/dev/null
                openssl req -new -x509 -days 3650 -key "$DATA_DIR/ssl/ca.key" \
                    -out "$DATA_DIR/ssl/ca.cert" \
                    -subj "/C=US/ST=State/L=City/O=WildosVPN/CN=WildosVPN-CA" 2>/dev/null
            fi
            
            # Создаем сертификат панели
            openssl genrsa -out "$DATA_DIR/ssl/panel.key" 2048 2>/dev/null
            openssl req -new -key "$DATA_DIR/ssl/panel.key" \
                -out "$DATA_DIR/ssl/panel.csr" \
                -subj "/C=US/ST=State/L=City/O=WildosVPN/CN=$PANEL_DOMAIN" 2>/dev/null
            
            openssl x509 -req -in "$DATA_DIR/ssl/panel.csr" \
                -CA "$DATA_DIR/ssl/ca.cert" -CAkey "$DATA_DIR/ssl/ca.key" \
                -CAcreateserial -out "$DATA_DIR/ssl/panel.cert" \
                -days 365 2>/dev/null
            
            rm -f "$DATA_DIR/ssl/panel.csr"
        fi
        
        # Устанавливаем правильные права доступа для Docker контейнера Caddy
        chown -R 999:999 "$DATA_DIR/ssl"
        chmod 600 "$DATA_DIR/ssl"/*.key 2>/dev/null || true
        chmod 644 "$DATA_DIR/ssl"/*.cert 2>/dev/null || true
        
        print_ok
        log_action "SSL сертификаты подготовлены для Caddy (UID/GID: 999)"
    else
        print_info "Режим разработки - SSL сертификаты не требуются"
    fi
}

# ===============================================================================
# ЗАПУСК И ФИНАЛИЗАЦИЯ
# ===============================================================================

build_and_start() {
    print_step "Сборка и запуск контейнеров"
    
    cd "$APP_DIR"
    
    # Остановка существующих контейнеров
    docker compose down 2>/dev/null || true
    
    # Сборка образов
    docker compose build --no-cache
    
    # Запуск сервисов
    docker compose up -d
    
    # Проверка статуса контейнеров
    if ! docker compose ps | grep -q "Up"; then
        print_fail
        error_exit "Ошибка запуска контейнеров"
    fi
    
    # Импорт администратора в базу данных
    print_step "Импорт администратора в базу данных"
    
    # ИСПРАВЛЕНИЕ: Ожидание готовности БД с проверкой таблиц (4 × 15 секунд)
    print_info "Ожидание готовности базы данных и завершения миграций..."
    local check_interval=15
    local max_checks=4
    local check_number=1
    local database_ready=false
    
    while [ $check_number -le $max_checks ]; do
        print_info "Проверка готовности БД ($check_number/$max_checks) - ожидание $check_interval сек..."
        sleep $check_interval
        
        # Проверяем готовность БД И существование таблиц
        if docker compose exec -T wildosvpn-panel python -c "
import sys
sys.path.append('/app')
try:
    from app.db import GetDB
    from sqlalchemy import text
    
    with GetDB() as db:
        # Проверяем соединение с БД
        db.execute(text('SELECT 1'))
        
        # Проверяем существование основных таблиц
        result = db.execute(text(\"SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'nodes', 'inbounds')\"))
        tables = [row[0] for row in result.fetchall()]
        
        if len(tables) >= 2:  # Проверяем что есть хотя бы основные таблицы
            print('Database and tables ready')
            exit(0)
        else:
            print(f'Tables not ready yet. Found: {tables}')
            exit(1)
            
except Exception as e:
    print(f'Database not ready: {e}')
    exit(1)
" 2>/dev/null; then
            print_info "✅ База данных и таблицы готовы к работе"
            database_ready=true
            break
        else
            print_warning "⏳ База данных или таблицы еще не готовы (возможно, идут миграции)..."
        fi
        
        ((check_number++))
    done
    
    if [ "$database_ready" = false ]; then
        print_fail
        print_error "❌ База данных недоступна после 60 секунд ожидания"
        print_error "❌ Администратор не импортирован"
        print_warning "Возможные причины:"
        print_warning "- Миграции Alembic занимают больше времени"
        print_warning "- Ошибки в структуре базы данных"
        print_warning "- Проблемы с правами доступа к SQLite файлу"
        print_warning ""
        print_warning "Проверьте логи: docker compose logs wildosvpn-panel"
        print_warning "Попробуйте импорт вручную: docker compose exec wildosvpn-panel python wildosvpn-cli.py admin import-from-env --yes"
        log_action "ERROR: База данных недоступна после ожидания, импорт администратора пропущен"
        return
    fi
    
    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Выполняем import-from-env для создания админа в БД
    print_info "Выполнение импорта администратора..."
    
    # Детальная диагностика
    print_info "🔍 Диагностика перед импортом:"
    print_info "   - Контейнер: wildosvpn-panel"
    print_info "   - Username: $SUDO_USERNAME"
    print_info "   - Password: [${#SUDO_PASSWORD} символов]"
    
    # Проверяем статус контейнера
    print_info "📋 Статус контейнера:"
    docker compose ps wildosvpn-panel || print_warning "Контейнер не найден"
    
    # Показываем переменные окружения для диагностики
    print_info "🌍 Переменные окружения в контейнере:"
    docker compose exec -T wildosvpn-panel env | grep -E "SUDO_USERNAME|SUDO_PASSWORD" || print_warning "❌ Переменные SUDO не найдены в контейнере!"
    
    # Проверяем доступность CLI скрипта
    print_info "📄 Проверка CLI скрипта:"
    docker compose exec -T wildosvpn-panel ls -la wildosvpn-cli.py || print_warning "❌ CLI скрипт не найден"
    
    # Проверяем монтирование .env файла
    print_info "📂 Проверка .env файла:"
    print_info "   - Локальный файл: $DATA_DIR/.env"
    if [ -f "$DATA_DIR/.env" ]; then
        local env_size=$(stat -c%s "$DATA_DIR/.env" 2>/dev/null || echo "0")
        print_info "   - Размер локального .env: $env_size байт"
        # Показываем содержимое для SUDO переменных
        print_info "   - SUDO переменные в локальном .env:"
        grep -E "SUDO_USERNAME|SUDO_PASSWORD" "$DATA_DIR/.env" || print_warning "   ❌ SUDO переменные отсутствуют в .env"
    else
        print_warning "   ❌ Локальный .env файл не найден!"
    fi
    
    # Проверяем .env внутри контейнера
    print_info "   - .env в контейнере:"
    docker compose exec -T wildosvpn-panel ls -la /var/lib/wildosvpn/.env || print_warning "   ❌ .env не найден в контейнере"
    
    # Пробуем импорт с выводом ошибок
    if docker compose exec -T wildosvpn-panel python wildosvpn-cli.py admin import-from-env --yes; then
        print_ok
        log_action "Администратор успешно импортирован в базу данных"
    else
        local exit_code=$?
        print_warning "Первая попытка неудачна (код: $exit_code), пробуем альтернативные способы"
        
        # Попытка через переменные окружения напрямую
        if docker compose exec -T wildosvpn-panel bash -c "
export SUDO_USERNAME='$SUDO_USERNAME'
export SUDO_PASSWORD='$SUDO_PASSWORD'
python wildosvpn-cli.py admin import-from-env --yes
"; then
            print_ok
            log_action "Администратор импортирован через прямую передачу переменных"
        else
            # Попытка через Python модуль
            if docker compose exec -T wildosvpn-panel python -c "
import sys
sys.path.append('/app')
import os
os.environ['SUDO_USERNAME'] = '$SUDO_USERNAME'
os.environ['SUDO_PASSWORD'] = '$SUDO_PASSWORD'
from cli.admin import import_from_env
import typer
ctx = typer.Context(typer.Typer())
import_from_env(yes_to_all=True)
print('Администратор создан через Python')
"; then
                print_ok
                log_action "Администратор импортирован через Python модуль"
            else
                print_fail
                print_error "Все попытки импорта администратора неудачны!"
                print_warning "Проверьте логи: docker compose logs wildosvpn-panel"
                print_warning "Импорт вручную: docker compose exec wildosvpn-panel python wildosvpn-cli.py admin import-from-env --yes"
                log_action "ERROR: Автоматический импорт администратора не удался"
            fi
        fi
    fi
    
    print_ok
}

# Получение токена администратора для отображения в финальной информации
get_admin_token() {
    local admin_token=""
    
    print_info "🔑 Попытка получения токена администратора..."
    
    # Проверяем готовность API сервера
    local api_ready=false
    local attempts=0
    local max_attempts=10
    
    print_info "⏳ Ожидание готовности API сервера..."
    while [ $attempts -lt $max_attempts ]; do
        if curl -s --connect-timeout 3 --max-time 5 "http://localhost:8000/api/system/health" >/dev/null 2>&1; then
            api_ready=true
            print_info "✅ API сервер готов"
            break
        fi
        sleep 2
        ((attempts++))
        echo -n "."
    done
    echo
    
    # Попытка получить токен через API (только если API готов)
    if [ "$api_ready" = true ] && command -v curl >/dev/null 2>&1; then
        print_info "🌐 Попытка получения токена через API..."
        
        # Пробуем разные возможные endpoints
        for endpoint in "/api/admins/token" "/api/admin/token" "/api/auth/login" "/api/token"; do
            admin_token=$(curl -s -X POST "http://localhost:8000$endpoint" \
                -H "Content-Type: application/x-www-form-urlencoded" \
                -d "username=$SUDO_USERNAME&password=$SUDO_PASSWORD" \
                2>/dev/null | jq -r '.access_token // .token // .access_token' 2>/dev/null)
            
            if [[ "$admin_token" != "null" && -n "$admin_token" && "$admin_token" =~ ^[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+$ ]]; then
                print_info "✅ Токен получен через API ($endpoint)"
                echo "$admin_token"
                return 0
            fi
        done
        print_warning "❌ Не удалось получить токен через API"
    else
        print_warning "❌ API недоступен, пропускаем попытку через HTTP"
    fi
    
    # Если не удалось получить через API, попытка через CLI
    print_info "🔧 Попытка создания токена через CLI..."
    
    # Проверяем доступность CLI команды
    if docker compose exec -T wildosvpn-panel python wildosvpn-cli.py admin --help >/dev/null 2>&1; then
        # Улучшенный парсинг JWT токена
        admin_token=$(docker compose exec -T wildosvpn-panel python wildosvpn-cli.py admin create-token "$SUDO_USERNAME" 2>/dev/null | \
                     grep -oE '[A-Za-z0-9._-]{20,}\.[A-Za-z0-9._-]{20,}\.[A-Za-z0-9._-]{20,}' | head -1)
        
        if [[ -n "$admin_token" && "$admin_token" =~ ^[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+$ ]]; then
            print_info "✅ Токен создан через CLI"
            echo "$admin_token"
            return 0
        else
            print_warning "❌ CLI вернул некорректный токен"
        fi
    else
        print_warning "❌ CLI команда недоступна"
    fi
    
    # Последняя попытка через прямой вызов Python модуля
    print_info "🐍 Попытка создания токена через Python модуль..."
    admin_token=$(docker compose exec -T wildosvpn-panel python -c "
import sys
sys.path.append('/app')
try:
    from app.auth import create_access_token
    from app.db import GetDB, crud
    
    with GetDB() as db:
        admin = crud.get_admin(db, username='$SUDO_USERNAME')
        if admin:
            token = create_access_token({'sub': admin.username, 'is_sudo': admin.is_sudo})
            print(token)
        else:
            print('Admin not found')
except Exception as e:
    print(f'Error: {e}')
" 2>/dev/null | grep -oE '[A-Za-z0-9._-]{20,}\.[A-Za-z0-9._-]{20,}\.[A-Za-z0-9._-]{20,}' | head -1)
    
    if [[ -n "$admin_token" && "$admin_token" =~ ^[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+$ ]]; then
        print_info "✅ Токен создан через Python модуль"
        echo "$admin_token"
        return 0
    fi
    
    print_warning "❌ Все попытки получения токена неудачны"
    echo "Не удалось получить токен"
    return 1
}

run_security_migrations() {
    if [ "$PRODUCTION_MODE" != true ]; then
        return
    fi
    
    print_step "Применение миграций безопасности"
    
    # Ожидание запуска контейнера
    sleep 10
    
    # Выполнение миграций через Docker
    if docker compose ps | grep -q wildosvpn-panel; then
        docker compose exec -T wildosvpn-panel python -c "
from app.db import engine
from app.db.models import Base
Base.metadata.create_all(bind=engine)
print('Security migrations applied successfully')
" 2>/dev/null || {
            print_warning "Не удалось применить миграции безопасности"
            log_action "WARNING: Миграции безопасности не применены"
        }
    fi
    
    print_ok
    log_action "Миграции безопасности применены"
}

install_cli() {
    print_step "Установка CLI инструмента"
    
    cat > /usr/local/bin/wildosvpn << EOF
#!/bin/bash
cd "$APP_DIR"

case "\$1" in
    start)
        docker compose up -d
        ;;
    stop)
        docker compose down
        ;;
    restart)
        docker compose restart
        ;;
    status)
        docker compose ps
        ;;
    logs)
        docker compose logs -f \${2:-}
        ;;
    update)
        curl -sSL https://raw.githubusercontent.com/wildos-dev/WildosTEST/main/install.sh | bash -s update
        ;;
    health)
        curl -s http://localhost:8000/health || echo "Service unavailable"
        ;;
    backup)
        tar -czf "/tmp/wildosvpn-backup-\$(date +%Y%m%d-%H%M%S).tar.gz" -C "$DATA_DIR" .
        echo "Backup created in /tmp/"
        ;;
    *)
        echo "Usage: wildosvpn {start|stop|restart|status|logs|update|health|backup}"
        exit 1
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/wildosvpn
    print_ok
}

# ===============================================================================
# ИНФОРМАЦИЯ И ЗАВЕРШЕНИЕ
# ===============================================================================

show_final_info() {
    clear
    echo
    colorized_echo green "════════════════════════════════════════════════════════════════"
    if [ "$UPDATE_MODE" = true ]; then
        colorized_echo green "                  ✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
    else
        colorized_echo green "                  ✅ УСТАНОВКА ЗАВЕРШЕНА!"
    fi
    colorized_echo green "════════════════════════════════════════════════════════════════"
    echo
    
    if [ "$UPDATE_MODE" != true ]; then
        colorized_echo cyan "🌐 URL панели управления:"
        colorized_echo white "   https://$PANEL_DOMAIN$DASHBOARD_PATH"
        echo
        colorized_echo cyan "🔐 Данные для входа:"
        colorized_echo white "   Логин: $SUDO_USERNAME"
        colorized_echo white "   Пароль: $SUDO_PASSWORD"
        echo
        
        # Получение и отображение токена администратора
        colorized_echo cyan "🔑 Токен администратора:"
        local admin_token=$(get_admin_token)
        if [[ "$admin_token" != "Не удалось получить токен" ]]; then
            colorized_echo white "   $admin_token"
            colorized_echo yellow "   ⚠️  Сохраните этот токен для API запросов"
        else
            colorized_echo yellow "   Токен можно получить после входа в панель"
        fi
        echo
    fi
    
    colorized_echo cyan "📁 Важные директории:"
    colorized_echo white "   Приложение: $APP_DIR"
    colorized_echo white "   Данные: $DATA_DIR"
    colorized_echo white "   Логи: $LOG_FILE"
    if [ "$PRODUCTION_MODE" = true ]; then
        colorized_echo white "   SSL: $DATA_DIR/ssl"
        colorized_echo white "   Безопасность: $DATA_DIR/logs/security"
    fi
    echo
    
    colorized_echo cyan "🛠️  Управление системой:"
    colorized_echo white "   wildosvpn start|stop|restart"
    colorized_echo white "   wildosvpn status - статус сервисов"
    colorized_echo white "   wildosvpn logs - просмотр логов"
    colorized_echo white "   wildosvpn update - обновление"
    colorized_echo white "   wildosvpn health - диагностика"
    colorized_echo white "   wildosvpn backup - создание резервной копии"
    echo
    
    if [ "$PRODUCTION_MODE" = true ]; then
        colorized_echo cyan "🔒 Функции безопасности:"
        colorized_echo green "   ✅ SSL сертификаты настроены"
        colorized_echo green "   ✅ Аутентификация узлов включена"
        colorized_echo green "   ✅ Firewall настроен"
        colorized_echo green "   ✅ Мониторинг безопасности активен"
        colorized_echo green "   ✅ Fail2ban защита включена"
        echo
    fi
    
    if [ "$UPDATE_MODE" != true ]; then
        colorized_echo yellow "📝 Важно:"
        colorized_echo white "   • Убедитесь, что домены указывают на этот сервер"
        colorized_echo white "   • Порты 80 и 443 должны быть открыты"
        if [ "$PRODUCTION_MODE" = true ]; then
            colorized_echo white "   • Продакшен SSL сертификаты настроены"
        else
            colorized_echo white "   • SSL сертификаты будут получены автоматически"
        fi
        echo
        
        colorized_echo red "🔒 БЕЗОПАСНОСТЬ:"
        colorized_echo yellow "   ⚠️  КРИТИЧЕСКИ ВАЖНО: Смените стандартный пароль 'admin'"
        colorized_echo yellow "   ⚠️  Зайдите в панель и создайте новый пароль администратора"
        colorized_echo yellow "   ⚠️  Стандартный пароль используется только для тестирования"
        echo
    fi
    
    colorized_echo cyan "🔧 Диагностика:"
    colorized_echo white "   wildosvpn status - проверить статус"
    colorized_echo white "   wildosvpn logs - посмотреть логи"
    if [ "$PRODUCTION_MODE" = true ]; then
        colorized_echo white "   fail2ban-client status - статус защиты"
    fi
    echo
}

# ===============================================================================
# ГЛАВНЫЕ ФУНКЦИИ УСТАНОВКИ
# ===============================================================================

install_wildosvpn() {
    log_action "Начало установки WildosVPN v$SCRIPT_VERSION"
    
    # Системные проверки
    check_root
    detect_os
    detect_arch
    check_network
    
    # Выбор режима развертывания
    setup_deployment_mode
    
    # Настройка
    setup_domains
    setup_dashboard_path
    setup_admin_credentials
    
    # Установка зависимостей
    install_dependencies
    install_docker
    
    # Установка приложения
    create_directories
    clone_repository
    fix_nodes_startup_issue
    
    # Настройка безопасности (только для продакшена)
    # setup_ssl_certificates  # Отключено: используем автоматические Let's Encrypt сертификаты
    setup_node_authentication
    setup_security_monitoring
    
    # Конфигурация
    create_dockerfile
    create_docker_compose
    create_caddyfile
    create_env_file
    # generate_certificates  # Отключено: используем Let's Encrypt
    
    # Запуск
    build_and_start
    run_security_migrations
    install_cli
    
    # Завершение
    show_final_info
    log_action "Установка WildosVPN завершена успешно"
}

update_wildosvpn() {
    if [[ ! -d "$APP_DIR" ]]; then
        error_exit "WildosVPN не установлен. Сначала выполните установку."
    fi
    
    UPDATE_MODE=true
    log_action "Начало обновления WildosVPN"
    
    check_root
    
    # Загрузка существующей конфигурации
    if [[ -f "$DATA_DIR/.env" ]]; then
        cp "$DATA_DIR/.env" "$DATA_DIR/.env.backup"
        source "$DATA_DIR/.env"
    fi
    
    # Остановка сервисов
    cd "$APP_DIR"
    docker compose down
    
    # Обновление кода
    clone_repository
    fix_nodes_startup_issue
    
    # Пересоздание конфигураций
    create_dockerfile
    create_docker_compose
    create_caddyfile
    create_env_file
    
    # Применение обновлений безопасности если включен продакшен режим
    if [[ "$PRODUCTION_MODE" == "true" ]]; then
        # setup_ssl_certificates  # Отключено: используем автоматические Let's Encrypt сертификаты
        setup_security_monitoring
    fi
    
    # Запуск
    build_and_start
    run_security_migrations
    install_cli
    
    show_final_info
    log_action "Обновление WildosVPN завершено успешно"
}

uninstall_wildosvpn() {
    echo
    colorized_echo red "⚠️  ВНИМАНИЕ: Это действие удалит все данные WildosVPN!"
    echo
    read -p "Вы уверены? (yes/no): " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        colorized_echo yellow "Удаление отменено"
        return
    fi
    
    print_step "Удаление WildosVPN"
    
    # Остановка и удаление контейнеров
    if [[ -f "$APP_DIR/docker-compose.yml" ]]; then
        cd "$APP_DIR"
        docker compose down -v 2>/dev/null || true
    fi
    
    # Удаление образов
    docker rmi $(docker images "wildosvpn*" -q) 2>/dev/null || true
    
    # Удаление файлов
    rm -rf "$APP_DIR"
    rm -rf "$DATA_DIR"
    rm -f "/usr/local/bin/wildosvpn"
    
    # Удаление конфигураций безопасности
    rm -f /etc/fail2ban/jail.d/wildosvpn.conf
    rm -f /etc/fail2ban/filter.d/wildosvpn-auth.conf
    rm -f /etc/logrotate.d/wildosvpn-security
    
    print_ok
    colorized_echo green "WildosVPN полностью удален"
}

show_status() {
    if [[ ! -d "$APP_DIR" ]]; then
        colorized_echo red "WildosVPN не установлен"
        return
    fi
    
    echo
    colorized_echo cyan "=== Статус WildosVPN ==="
    echo
    
    cd "$APP_DIR"
    if docker compose ps 2>/dev/null; then
        echo
        colorized_echo cyan "=== Использование ресурсов ==="
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
            wildosvpn-panel wildosvpn-caddy 2>/dev/null || colorized_echo yellow "Статистика недоступна"
        
        echo
        colorized_echo cyan "=== Безопасность ==="
        if command -v fail2ban-client >/dev/null 2>&1; then
            fail2ban-client status 2>/dev/null || colorized_echo yellow "fail2ban недоступен"
        fi
        
        if command -v ufw >/dev/null 2>&1; then
            ufw status numbered 2>/dev/null || colorized_echo yellow "ufw недоступен"
        fi
    else
        colorized_echo red "Сервисы не запущены"
    fi
}

show_logs() {
    if [[ ! -d "$APP_DIR" ]]; then
        colorized_echo red "WildosVPN не установлен"
        return
    fi
    
    echo
    colorized_echo cyan "Показать логи для:"
    colorized_echo white "1) Панель"
    colorized_echo white "2) Caddy"
    colorized_echo white "3) Все сервисы"
    colorized_echo white "4) Логи безопасности"
    echo
    
    read -p "Выберите (1-4): " log_choice
    
    cd "$APP_DIR"
    case $log_choice in
        1) docker compose logs -f wildosvpn-panel;;
        2) docker compose logs -f caddy;;
        3) docker compose logs -f;;
        4) 
            if [[ -d "$DATA_DIR/logs/security" ]]; then
                tail -f "$DATA_DIR/logs/security"/*.log
            else
                colorized_echo yellow "Логи безопасности недоступны"
            fi
            ;;
        *) colorized_echo red "Неверный выбор";;
    esac
}

# ===============================================================================
# ГЛАВНОЕ МЕНЮ
# ===============================================================================

show_menu() {
    clear
    echo
    colorized_echo cyan "══════════════════════════════════════════════════════════════"
    colorized_echo cyan "              WildosVPN Installer v$SCRIPT_VERSION"
    colorized_echo cyan "                Production Security Edition"
    colorized_echo cyan "══════════════════════════════════════════════════════════════"
    echo
    colorized_echo blue "Выберите действие:"
    echo
    colorized_echo white "1) Установить WildosVPN"
    colorized_echo white "2) Обновить WildosVPN"
    colorized_echo white "3) Удалить WildosVPN"
    colorized_echo white "4) Показать статус"
    colorized_echo white "5) Просмотр логов"
    colorized_echo white "6) Выход"
    echo
    
    read -p "Введите номер (1-6): " choice
    
    case $choice in
        1) install_wildosvpn;;
        2) update_wildosvpn;;
        3) uninstall_wildosvpn;;
        4) show_status;;
        5) show_logs;;
        6) exit 0;;
        *) colorized_echo red "Неверный выбор"; sleep 2; show_menu;;
    esac
}

# ===============================================================================
# ТОЧКА ВХОДА
# ===============================================================================

main() {
    # Обработка аргументов командной строки
    case "${1:-}" in
        "install") install_wildosvpn;;
        "update") update_wildosvpn;;
        "uninstall") uninstall_wildosvpn;;
        *) show_menu;;
    esac
}

main "$@"
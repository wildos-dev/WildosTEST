#!/usr/bin/env bash
# production_node_setup.sh - Продакшен установка WildosNode с безопасностью
# Версия: 4.0.0 - Enhanced Security for External Servers

set -e

# ===============================================================================
# Production Configuration
# ===============================================================================
SCRIPT_VERSION="4.0.0"
APP_NAME="wildosnode"
REPO_URL="https://github.com/wildos-dev/WildosTEST"
REPO_BRANCH="main"

# Директории
INSTALL_DIR="/opt/$APP_NAME"
DATA_DIR="/var/lib/$APP_NAME"
SSL_DIR="$DATA_DIR/ssl"
CONFIG_DIR="$DATA_DIR/configs"
COMPOSE_DIR="/opt/wildosvpn"
LOG_DIR="/var/log/$APP_NAME"
DOCKER_COMPOSE_FILE="$COMPOSE_DIR/docker-compose.node.yml"

# Режим обновления
UPDATE_MODE=false

# Продакшен настройки по умолчанию
DEFAULT_PORT="62050"
DEFAULT_HOST="0.0.0.0"
DEFAULT_USE_SSL="true"
DEFAULT_PRODUCTION_MODE="true"

# ===============================================================================
# Color scheme
# ===============================================================================
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m'

# Функции вывода
colorized_echo() {
    local color=$1
    local text=$2
    case $color in
        "red") printf "${RED}${text}${NC}\n" ;;
        "green") printf "${GREEN}${text}${NC}\n" ;;
        "yellow") printf "${YELLOW}${text}${NC}\n" ;;
        "blue") printf "${BLUE}${text}${NC}\n" ;;
        "cyan") printf "${CYAN}${text}${NC}\n" ;;
        "white") printf "${WHITE}${text}${NC}\n" ;;
        "bold") printf "${BOLD}${text}${NC}\n" ;;
        *) echo "${text}" ;;
    esac
}

print_step() { echo -ne "${CYAN}→ $1...${NC}"; }
print_ok() { echo -e " ${GREEN}✓${NC}"; }
print_fail() { echo -e " ${RED}✗${NC}"; }
print_warning() { colorized_echo yellow "⚠️  $1"; }
print_error() { colorized_echo red "❌ $1"; }
print_success() { colorized_echo green "✅ $1"; }
print_info() { colorized_echo blue "ℹ️  $1"; }

# ===============================================================================
# Production SSL Certificate Management
# ===============================================================================

# Простая проверка SSL файлов
verify_ssl_files() {
    local ssl_files=("$SSL_DIR/node.cert" "$SSL_DIR/node.key" "$SSL_DIR/ca.cert")
    
    for file in "${ssl_files[@]}"; do
        if [[ ! -s "$file" ]]; then
            return 1
        fi
    done
    
    return 0
}

# Получить сертификат от панели управления (упрощённая версия)
get_certificate_from_panel() {
    local panel_url="$1"
    local node_id="$2"
    local hostname="$3"
    local token="$4"
    
    print_step "Получение SSL сертификата от панели"
    
    # Получить IP адрес
    local ip_address=$(curl -s --connect-timeout 5 --max-time 10 https://api.ipify.org 2>/dev/null || echo "")
    
    # Подготовить JSON запрос
    local json_request=$(cat <<EOF
{
    "node_id": $node_id,
    "hostname": "$hostname",
    "ip_address": "$ip_address"
}
EOF
)
    
    # Выполнить запрос с retry логикой
    local max_attempts=3
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        print_info "Попытка $attempt из $max_attempts..."
        
        local response=$(curl -s -w "\n%{http_code}" \
            --connect-timeout 10 --max-time 30 \
            -X POST "$panel_url/api/nodes/generate-certificate" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $token" \
            -d "$json_request" 2>/dev/null)
        
        local exit_code=$?
        local http_code=$(echo "$response" | tail -n1)
        local response_body=$(echo "$response" | head -n -1)
        
        # Проверить успешность запроса
        if [[ $exit_code -eq 0 && ("$http_code" == "200" || "$http_code" == "201") ]]; then
            # Извлечь сертификаты из ответа
            local node_cert=""
            local ca_cert=""
            
            if [[ "$USE_JQ" == "true" ]]; then
                node_cert=$(echo "$response_body" | jq -r '.certificate' 2>/dev/null)
                ca_cert=$(echo "$response_body" | jq -r '.ca_certificate' 2>/dev/null)
            else
                # Простой парсинг для извлечения сертификатов
                node_cert=$(echo "$response_body" | grep -o '"certificate"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4 | head -1)
                ca_cert=$(echo "$response_body" | grep -o '"ca_certificate"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4 | head -1)
            fi
            
            # Извлечь приватный ключ из ответа
            local node_key=""
            if [[ "$USE_JQ" == "true" ]]; then
                node_key=$(echo "$response_body" | jq -r '.private_key // .key // empty' 2>/dev/null)
            else
                # Простой парсинг для извлечения приватного ключа
                node_key=$(echo "$response_body" | grep -o '"private_key"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4 | head -1)
                if [[ -z "$node_key" ]]; then
                    node_key=$(echo "$response_body" | grep -o '"key"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4 | head -1)
                fi
            fi
            
            if [[ "$node_cert" != "null" && "$ca_cert" != "null" && -n "$node_cert" && -n "$ca_cert" ]]; then
                # Сохранить сертификаты
                echo "$node_cert" > "$SSL_DIR/node.cert"
                echo "$ca_cert" > "$SSL_DIR/ca.cert"
                
                if [[ "$node_key" != "null" && -n "$node_key" ]]; then
                    # Сохранить приватный ключ от панели
                    echo "$node_key" > "$SSL_DIR/node.key"
                    print_success "Получены сертификат, CA и приватный ключ от панели"
                else
                    # Генерировать временный приватный ключ (fallback)
                    print_warning "Панель не вернула приватный ключ, генерируем локально"
                    openssl genrsa -out "$SSL_DIR/node.key" 2048 2>/dev/null
                fi
                
                # Установить права доступа
                chmod 600 "$SSL_DIR/node.key"
                chmod 640 "$SSL_DIR/node.cert"
                chmod 640 "$SSL_DIR/ca.cert"
                
                print_ok >&2
                print_success "SSL сертификат успешно получен от панели"
                return 0
            else
                print_error "Неверный формат ответа API: отсутствуют сертификаты"
                print_info "Ответ API: $response_body"
            fi
            break
        else
            print_warning "Попытка $attempt не удалась (HTTP: $http_code, Exit: $exit_code)"
            if [[ -n "$response_body" ]]; then
                local short_response=$(echo "$response_body" | head -c 200)
                print_info "Ответ сервера: $short_response"
            fi
            
            # Если это ошибка валидации (422), не повторяем
            if [[ "$http_code" == "422" ]]; then
                print_error "API не принимает параметры"
                break
            fi
            
            # Экспоненциальная задержка перед повтором
            if [[ $attempt -lt $max_attempts ]]; then
                local delay=$((2 ** attempt))
                print_info "Повтор через $delay секунд..."
                sleep $delay
            fi
        fi
        
        ((attempt++))
    done
    
    print_fail
    print_error "Не удалось получить сертификат от панели после $max_attempts попыток"
    return 1
}

# Генерировать самоподписанный сертификат как fallback (улучшенная версия)
generate_selfsigned_certificate() {
    local hostname="$1"
    
    print_step "Генерация самоподписанного SSL сертификата"
    
    # Создать приватный ключ с лучшей энтропией
    if ! openssl genrsa -out "$SSL_DIR/node.key" 4096 2>/dev/null; then
        print_fail
        print_error "Не удалось создать приватный ключ"
        return 1
    fi
    
    # Создать конфигурационный файл для расширений
    local temp_config="/tmp/ssl_config_${node_id}.conf"
    cat > "$temp_config" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C=US
ST=State
L=City
O=WildosVPN
CN=$hostname

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $hostname
DNS.2 = localhost
IP.1 = 127.0.0.1
EOF
    
    # Создать самоподписанный сертификат с расширениями
    if ! openssl req -new -x509 -key "$SSL_DIR/node.key" \
        -out "$SSL_DIR/node.cert" -days 365 \
        -config "$temp_config" \
        -extensions v3_req 2>/dev/null; then
        print_fail
        print_error "Не удалось создать сертификат"
        rm -f "$temp_config"
        return 1
    fi
    
    # Скопировать как CA для совместимости
    cp "$SSL_DIR/node.cert" "$SSL_DIR/ca.cert"
    
    # Установить безопасные права доступа
    chmod 600 "$SSL_DIR/node.key"
    chmod 640 "$SSL_DIR/node.cert"
    chmod 640 "$SSL_DIR/ca.cert"
    
    # Валидировать созданный сертификат
    if validate_certificate "$SSL_DIR/node.cert" "$hostname"; then
        # Очистить временный файл
        rm -f "$temp_config"
        
        print_ok >&2
        print_warning "Использован самоподписанный сертификат (не рекомендуется для продакшена)"
        print_info "Срок действия: 365 дней"
        return 0
    else
        rm -f "$temp_config"
        return 1
    fi
}

# Проверить готовность SSL инфраструктуры
verify_ssl_setup() {
    local hostname="${1:-127.0.0.1}"
    print_step "Проверка SSL конфигурации"
    
    # Проверить наличие основных SSL файлов
    if ! verify_ssl_files; then
        print_fail
        print_error "Отсутствуют необходимые SSL файлы"
        return 1
    fi
    
    # Установить правильные права доступа
    chmod 600 "$SSL_DIR/node.key" 2>/dev/null
    chmod 640 "$SSL_DIR/node.cert" "$SSL_DIR/ca.cert" 2>/dev/null
    
    print_ok >&2
    print_success "SSL инфраструктура готова к использованию"
    return 0
}

# ===============================================================================  
# JSON Parsing без зависимостей
# ===============================================================================

# Функция для извлечения значения из JSON без jq
extract_json_value() {
    local json="$1"
    local key="$2"
    
    # Простой парсинг JSON для извлечения числовых ID
    local value=$(echo "$json" | sed -n "s/.*\"$key\"[[:space:]]*:[[:space:]]*\([0-9]\+\).*/\1/p")
    
    # Если простой метод не сработал, используем более детальный поиск
    if [[ -z "$value" ]]; then
        value=$(echo "$json" | grep -o "\"$key\"[[:space:]]*:[[:space:]]*[0-9]\+" | grep -o "[0-9]\+")
    fi
    
    echo "$value"
}

# Проверка и установка зависимостей
check_and_install_dependencies() {
    print_step "Проверка зависимостей"
    
    local missing_deps=()
    
    # Проверить основные утилиты
    local required_commands=("curl" "openssl" "docker")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
        fi
    done
    
    # Проверка Docker Compose (поддерживаем обе версии)
    local has_docker_compose=false
    if command -v docker >/dev/null 2>&1; then
        # Проверить новую версию (docker compose как плагин)
        if docker compose version >/dev/null 2>&1; then
            print_info "Найден Docker Compose (плагин): $(docker compose version --short 2>/dev/null || echo "установлен")"
            has_docker_compose=true
        # Проверить старую версию (docker-compose как отдельная утилита)
        elif command -v docker-compose >/dev/null 2>&1; then
            print_info "Найден Docker Compose (отдельная утилита): $(docker-compose version --short 2>/dev/null || echo "установлен")"
            has_docker_compose=true
        fi
    fi
    
    if [[ "$has_docker_compose" == "false" ]]; then
        missing_deps+=("docker-compose")
    fi
    
    # jq опционально - если есть, используем, если нет - используем bash парсинг
    if command -v jq >/dev/null 2>&1; then
        print_info "jq найден - будет использоваться для парсинга JSON"
        USE_JQ=true
    else
        print_warning "jq не найден - будет использоваться встроенный парсинг JSON"
        USE_JQ=false
    fi
    
    if [[ ${#missing_deps[@]} -eq 0 ]]; then
        print_ok >&2
        return 0
    fi
    
    print_fail
    print_error "Отсутствуют необходимые зависимости:"
    for dep in "${missing_deps[@]}"; do
        print_error "  - $dep"
    done
    
    # Попытаться установить автоматически
    print_info "Попытка автоматической установки..."
    
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update >/dev/null 2>&1
        for dep in "${missing_deps[@]}"; do
            case "$dep" in
                "docker")
                    curl -fsSL https://get.docker.com -o get-docker.sh
                    sh get-docker.sh
                    rm get-docker.sh
                    systemctl enable docker
                    systemctl start docker
                    ;;
                "docker-compose")
                    # Устанавливаем Docker Compose как плагин (современный способ)
                    print_info "Установка Docker Compose плагина..."
                    apt-get install -y docker-compose-plugin
                    
                    # Проверяем успешность установки
                    if docker compose version >/dev/null 2>&1; then
                        print_info "Docker Compose плагин успешно установлен"
                    else
                        print_warning "Плагин не установился, пробуем установить отдельную утилиту..."
                        apt-get install -y docker-compose
                    fi
                    ;;
                *)
                    apt-get install -y "$dep"
                    ;;
            esac
        done
        print_success "Зависимости установлены"
        return 0
    elif command -v yum >/dev/null 2>&1; then
        for dep in "${missing_deps[@]}"; do
            case "$dep" in
                "docker")
                    # Установка Docker на CentOS/RHEL
                    yum install -y yum-utils
                    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                    yum install -y docker-ce docker-ce-cli containerd.io
                    systemctl enable docker
                    systemctl start docker
                    ;;
                "docker-compose")
                    # На RHEL/CentOS сначала пробуем плагин
                    print_info "Установка Docker Compose..."
                    yum install -y docker-compose-plugin 2>/dev/null || {
                        print_warning "Плагин недоступен, устанавливаем отдельную утилиту..."
                        # Fallback к установке отдельной утилиты
                        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
                        chmod +x /usr/local/bin/docker-compose
                        ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose 2>/dev/null || true
                    }
                    ;;
                *)
                    yum install -y "$dep"
                    ;;
            esac
        done
        print_success "Зависимости установлены"
        return 0
    else
        print_error "Не удалось автоматически установить зависимости"
        print_error "Установите вручную: ${missing_deps[*]}"
        return 1
    fi
}

# ===============================================================================
# Docker Compose Management  
# ===============================================================================

# Функция для умного выполнения команд Docker Compose
run_docker_compose() {
    local compose_args="$*"
    
    # Проверяем доступность новой версии (плагин)
    if docker compose version >/dev/null 2>&1; then
        docker compose $compose_args
    # Fallback к старой версии (отдельная утилита)
    elif command -v docker-compose >/dev/null 2>&1; then
        docker-compose $compose_args
    else
        print_error "Docker Compose не найден! Установите docker-compose или docker-compose-plugin"
        return 1
    fi
}

# ===============================================================================
# Node Authentication
# ===============================================================================

# Получить токен аутентификации от панели
get_node_token() {
    local panel_url="$1"
    local node_id="$2"
    local admin_token="$3"
    
    print_step "Получение токена аутентификации узла" >&2
    
    local token_request=$(cat <<EOF
{
    "node_id": $node_id
}
EOF
)
    
    local response=$(curl -s -X POST "$panel_url/api/nodes/generate-token" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $admin_token" \
        -d "$token_request" 2>/dev/null)
    
    if [[ $? -eq 0 && -n "$response" ]]; then
        local node_token=""
        
        if [[ "$USE_JQ" == "true" ]]; then
            node_token=$(echo "$response" | jq -r '.token' 2>/dev/null)
        else
            # Извлекаем токен используя простой парсинг
            node_token=$(echo "$response" | grep -o '"token"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)
        fi
        
        if [[ "$node_token" != "null" && -n "$node_token" ]]; then
            echo "$node_token"
            print_ok >&2
            return 0
        fi
    fi
    
    print_fail >&2
    print_error "Не удалось получить токен аутентификации" >&2
    return 1
}

# ===============================================================================
# Network Configuration
# ===============================================================================

# Получить сетевую конфигурацию узла (IP и порт)
get_node_network_config() {
    colorized_echo yellow "=== Конфигурация сети узла ==="
    echo
    
    # Определить внешний IP автоматически
    print_step "Определение внешнего IP адреса"
    local detected_ip=$(curl -s --connect-timeout 5 --max-time 10 https://api.ipify.org 2>/dev/null)
    if [[ -z "$detected_ip" ]]; then
        detected_ip=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
    fi
    print_ok >&2
    print_info "Определён IP: $detected_ip"
    echo
    
    # Запросить IP у пользователя
    colorized_echo white "IP адрес узла:"
    colorized_echo white "  Этот адрес будет использоваться клиентами для подключения к узлу"
    colorized_echo white "  По умолчанию: $detected_ip (автоопределение)"
    echo
    read -p "Введите IP адрес узла (или нажмите Enter для '$detected_ip'): " user_ip
    
    local node_ip="$detected_ip"
    if [[ -n "$user_ip" ]]; then
        # Простая валидация IP адреса
        if [[ "$user_ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
            node_ip="$user_ip"
            print_info "Использован пользовательский IP: $node_ip"
        else
            print_warning "Некорректный формат IP адреса, использован автоопределённый: $detected_ip"
        fi
    else
        print_info "Использован автоопределённый IP: $node_ip"
    fi
    echo
    
    # Запросить порт у пользователя
    colorized_echo white "Порт узла:"
    colorized_echo white "  Стандартный порт WildosVPN: $DEFAULT_PORT"
    colorized_echo white "  Убедитесь что порт открыт в firewall"
    echo
    read -p "Введите порт узла (или нажмите Enter для '$DEFAULT_PORT'): " user_port
    
    local node_port="$DEFAULT_PORT"
    if [[ -n "$user_port" ]]; then
        # Валидация порта (1-65535)
        if [[ "$user_port" =~ ^[0-9]+$ && "$user_port" -ge 1 && "$user_port" -le 65535 ]]; then
            node_port="$user_port"
            print_info "Использован пользовательский порт: $node_port"
        else
            print_warning "Некорректный порт, использован стандартный: $DEFAULT_PORT"
        fi
    else
        print_info "Использован стандартный порт: $node_port"
    fi
    echo
    
    # Проверка доступности порта
    print_step "Проверка доступности порта $node_port"
    if command -v netstat >/dev/null 2>&1; then
        if netstat -ln 2>/dev/null | grep -q ":$node_port "; then
            print_fail
            print_warning "Порт $node_port уже используется другим процессом"
            print_warning "Убедитесь что он будет доступен для WildosNode"
        else
            print_ok >&2
        fi
    else
        print_warning "netstat недоступен, пропускаем проверку порта"
    fi
    echo
    
    # Вывести итоговую конфигурацию
    colorized_echo green "✅ Сетевая конфигурация узла:"
    colorized_echo white "   IP адрес: $node_ip"
    colorized_echo white "   Порт:     $node_port"
    echo
    
    # Подтверждение от пользователя
    read -p "Продолжить установку с этими настройками? (y/n): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" && "$confirm" != "да" ]]; then
        print_error "Установка прервана пользователем"
        exit 1
    fi
    echo
    
    # Вернуть значения через глобальные переменные
    NODE_IP="$node_ip"
    NODE_PORT="$node_port"
    
    print_success "Сетевая конфигурация принята"
}

# ===============================================================================
# Production Installation
# ===============================================================================

install_production_node() {
    local panel_url="$1"
    local node_name="$2"
    local hostname="$3"
    local admin_token="$4"
    
    colorized_echo cyan "=== Установка WildosNode в продакшен режиме ==="
    
    # 1. Проверить и установить зависимости
    check_and_install_dependencies || exit 1
    
    # 2. Получить сетевую конфигурацию от пользователя
    get_node_network_config
    
    # 3. Создать структуру директорий
    create_directories
    
    # 4. Получить код
    download_source_code
    
    # 5. Создать Dockerfile для локальной сборки
    create_wildosnode_dockerfile
    
    # 6. Создать узел в панели (получить node_id)
    print_info "Создание узла '$node_name' в панели управления..."
    echo "DEBUG: Вызываем create_node_in_panel с параметрами:"
    echo "DEBUG:   panel_url='$panel_url'"  
    echo "DEBUG:   node_name='$node_name'"
    echo "DEBUG:   admin_token='${admin_token:0:20}...'"
    echo "DEBUG:   NODE_IP='$NODE_IP'"
    echo "DEBUG:   NODE_PORT='$NODE_PORT'"
    
    local node_id=$(create_node_in_panel "$panel_url" "$node_name" "$admin_token" "$NODE_IP" "$NODE_PORT")
    echo "DEBUG: create_node_in_panel вернул: '$node_id'"
    
    if [[ -z "$node_id" || ! "$node_id" =~ ^[0-9]+$ ]]; then
        print_error "Критическая ошибка: не удалось создать узел в панели"
        print_error "Полученный результат: '$node_id'"
        print_error "Проверьте:"
        print_error "  - Доступность панели: $panel_url"
        print_error "  - Корректность токена администратора"
        print_error "  - Подключение к интернету"
        exit 1
    fi
    print_info "Узел успешно создан с ID: $node_id"
    
    # 7. Получить SSL сертификат от панели
    mkdir -p "$SSL_DIR"
    print_info "Ожидание готовности API панели..."
    sleep 3  # Дать время API обработать созданный узел
    
    print_info "Запрос SSL сертификата для узла ID: $node_id"
    if get_certificate_from_panel "$panel_url" "$node_id" "$hostname" "$admin_token"; then
        print_success "SSL сертификат успешно получен от панели"
    else
        print_warning "Не удалось получить сертификат от панели. Генерация самоподписанного..."
        if generate_selfsigned_certificate "$hostname"; then
            print_warning "Используется самоподписанный сертификат (не рекомендуется для продакшена)"
        else
            print_error "Критическая ошибка: не удалось создать ни один сертификат"
            print_error "Установка невозможна без SSL сертификата"
            exit 1
        fi
    fi
    
    # 8. Проверить готовность SSL инфраструктуры
    if ! verify_ssl_setup "$hostname"; then
        print_error "SSL инфраструктура не готова. Установка невозможна."
        exit 1
    fi
    
    # 9. Получить токен аутентификации
    print_info "Генерация токена аутентификации для узла..."
    local node_token=$(get_node_token "$panel_url" "$node_id" "$admin_token")
    if [[ -z "$node_token" ]]; then
        print_error "Критическая ошибка: не удалось получить токен аутентификации"
        print_error "Узел создан в панели, но не может быть аутентифицирован"
        exit 1
    fi
    print_success "Токен аутентификации получен"
    
    # 10. Создать конфигурацию с пользовательскими сетевыми настройками
    print_info "Создание продакшен конфигурации..."
    create_production_config "$node_id" "$panel_url" "$hostname" "$node_token" "$NODE_PORT"
    
    # 11. Создать Docker Compose с пользовательскими настройками
    print_info "Подготовка Docker окружения..."
    create_production_docker_compose "$NODE_PORT"
    
    # 12. Собрать и запустить сервис
    print_info "Запуск продакшен сервиса..."
    start_production_service
    
    print_success "WildosNode успешно установлен в продакшен режиме!"
    
    # Вывести итоговую информацию об узле
    colorized_echo green "📋 Информация о установленном узле:"
    colorized_echo white "   Имя узла:     $node_name"
    colorized_echo white "   ID в панели:  $node_id"
    colorized_echo white "   IP адрес:     $NODE_IP"
    colorized_echo white "   Порт:         $NODE_PORT"
    colorized_echo white "   Панель:       $panel_url"
    echo
    colorized_echo cyan "🔗 Для подключения клиентов используйте:"
    colorized_echo white "   Адрес сервера: $NODE_IP:$NODE_PORT"
    echo
    
    show_production_status "$panel_url" "$node_id"
}

# ===============================================================================
# Update Functions
# ===============================================================================

# Обновление WildosNode
update_wildosnode() {
    if [[ ! -d "$INSTALL_DIR" || ! -f "$DATA_DIR/.env" ]]; then
        print_error "WildosNode не установлен. Сначала выполните установку."
        exit 1
    fi
    
    UPDATE_MODE=true
    
    colorized_echo cyan "=== Обновление WildosNode ==="
    echo
    
    print_info "Создание резервной копии конфигурации..."
    backup_configuration
    
    print_info "Загрузка существующей конфигурации..."
    load_existing_configuration
    
    print_info "Остановка сервиса..."
    stop_node_service
    
    print_info "Обновление исходного кода..."
    update_source_code
    
    print_info "Пересоздание конфигурации..."
    recreate_configuration
    
    print_info "Запуск обновленного сервиса..."
    start_production_service
    
    print_success "Обновление WildosNode завершено!"
    
    print_info "Информация об обновленном узле:"
    show_update_status
}

# Создать резервную копию конфигурации
backup_configuration() {
    print_step "Создание резервной копии"
    
    local backup_dir="$DATA_DIR/backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Бэкап .env файла
    if [[ -f "$DATA_DIR/.env" ]]; then
        cp "$DATA_DIR/.env" "$backup_dir/.env"
        cp "$DATA_DIR/.env" "$DATA_DIR/.env.backup"
    fi
    
    # Бэкап SSL сертификатов
    if [[ -d "$SSL_DIR" ]]; then
        cp -r "$SSL_DIR" "$backup_dir/ssl"
    fi
    
    # Бэкап docker-compose файла
    if [[ -f "$DOCKER_COMPOSE_FILE" ]]; then
        cp "$DOCKER_COMPOSE_FILE" "$backup_dir/docker-compose.node.yml"
    fi
    
    print_ok >&2
    print_info "Резервная копия создана: $backup_dir"
}

# Загрузить существующую конфигурацию
load_existing_configuration() {
    print_step "Загрузка конфигурации"
    
    if [[ -f "$DATA_DIR/.env" ]]; then
        # Извлечь важные параметры из существующего .env
        NODE_ID=$(grep "^NODE_ID=" "$DATA_DIR/.env" | cut -d'=' -f2 2>/dev/null || echo "")
        HOSTNAME=$(grep "^HOSTNAME=" "$DATA_DIR/.env" | cut -d'=' -f2 2>/dev/null || echo "")
        SERVICE_PORT=$(grep "^SERVICE_PORT=" "$DATA_DIR/.env" | cut -d'=' -f2 2>/dev/null || echo "$DEFAULT_PORT")
        PANEL_URL=$(grep "^PANEL_URL=" "$DATA_DIR/.env" | cut -d'=' -f2 2>/dev/null || echo "")
        NODE_TOKEN=$(grep "^NODE_TOKEN=" "$DATA_DIR/.env" | cut -d'=' -f2 2>/dev/null || echo "")
        
        # Установить глобальные переменные для использования в других функциях
        NODE_IP=$(curl -s --connect-timeout 5 --max-time 10 https://api.ipify.org 2>/dev/null || echo "127.0.0.1")
        NODE_PORT="$SERVICE_PORT"
        
        print_ok >&2
        print_info "Конфигурация загружена: Node ID=$NODE_ID, Port=$SERVICE_PORT"
    else
        print_fail >&2
        print_error "Файл конфигурации не найден"
        exit 1
    fi
}

# Остановить сервис
stop_node_service() {
    print_step "Остановка сервиса WildosNode"
    
    if [[ -f "$DOCKER_COMPOSE_FILE" ]]; then
        cd "$COMPOSE_DIR"
        run_docker_compose -f "$DOCKER_COMPOSE_FILE" down 2>/dev/null || true
        
        # Дополнительно убедиться что контейнер остановлен
        docker stop wildosnode-production 2>/dev/null || true
        docker rm wildosnode-production 2>/dev/null || true
        
        print_ok >&2
    else
        print_warning "Docker Compose файл не найден, пропускаем остановку"
    fi
}

# Обновить исходный код
update_source_code() {
    print_step "Обновление исходного кода"
    
    cd "$INSTALL_DIR"
    if [[ -d ".git" ]]; then
        # Если это git репозиторий, обновляем
        git fetch origin >&2 2>&1
        git reset --hard origin/$REPO_BRANCH >&2 2>&1
        git pull origin $REPO_BRANCH >&2 2>&1
        print_ok >&2
    else
        # Если не git, скачиваем заново
        print_warning "Git репозиторий не найден, скачиваем код заново..."
        rm -rf "$INSTALL_DIR"
        download_source_code
        print_ok >&2
    fi
}

# Пересоздать конфигурацию с сохранением параметров
recreate_configuration() {
    print_step "Пересоздание конфигурации"
    
    # Создать новый Dockerfile
    create_wildosnode_dockerfile
    
    # Создать .env файл с сохраненными параметрами
    create_production_config "$NODE_ID" "$PANEL_URL" "$HOSTNAME" "$NODE_TOKEN" "$NODE_PORT"
    
    # Создать docker-compose файл
    create_production_docker_compose "$NODE_PORT"
    
    print_ok >&2
}

# Показать статус после обновления
show_update_status() {
    echo
    colorized_echo green "✅ Обновление завершено успешно!"
    echo
    
    print_info "Параметры узла:"
    echo "  Node ID:     $NODE_ID"
    echo "  Hostname:    $HOSTNAME" 
    echo "  IP:Port:     $NODE_IP:$NODE_PORT"
    echo "  Panel URL:   $PANEL_URL"
    echo
    
    print_info "Статус сервиса:"
    run_docker_compose -f "$DOCKER_COMPOSE_FILE" ps
    echo
    
    print_info "Последние логи:"
    run_docker_compose -f "$DOCKER_COMPOSE_FILE" logs --tail 10
}

# Создать узел в панели управления (улучшенная версия)
create_node_in_panel() {
    local panel_url="$1"
    local node_name="$2"
    local admin_token="$3"
    local node_ip="$4"
    local node_port="$5"
    
    echo "DEBUG: Внутри create_node_in_panel" >&2
    print_step "Регистрация узла в панели управления" >&2
    print_info "IP: $node_ip, Порт: $node_port" >&2
    
    local create_request=$(cat <<EOF
{
    "name": "$node_name",
    "address": "$node_ip",
    "port": $node_port,
    "connection_backend": "grpclib"
}
EOF
)
    
    # Выполнить запрос с retry логикой
    local max_attempts=3
    local attempt=1
    local node_id=""
    
    while [[ $attempt -le $max_attempts ]]; do
        print_info "Попытка создания узла $attempt из $max_attempts..." >&2
        
        local response=$(curl -s -w "\n%{http_code}" \
            --connect-timeout 10 --max-time 30 \
            -X POST "$panel_url/api/nodes" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $admin_token" \
            -d "$create_request" 2>/dev/null)
        
        local exit_code=$?
        local http_code=$(echo "$response" | tail -n1)
        local response_body=$(echo "$response" | head -n -1)
        
        # Проверить успешность запроса (принимаем 200, 201 и даже 500 если узел создался)
        if [[ $exit_code -eq 0 && ("$http_code" == "200" || "$http_code" == "201" || "$http_code" == "500") ]]; then
            echo "DEBUG: API ответил с HTTP $http_code" >&2
            echo "DEBUG: Тело ответа: ${response_body:0:300}$([ ${#response_body} -gt 300 ] && echo "...")" >&2
            
            # Попытаться извлечь node_id из ответа - используем все возможные методы
            local node_id=""
            
            # Метод 1: jq если доступен
            if command -v jq >/dev/null 2>&1; then
                node_id=$(echo "$response_body" | jq -r '.id' 2>/dev/null)
                echo "DEBUG: jq результат: '$node_id'" >&2
            fi
            
            # Метод 2: простой sed парсинг если jq не сработал
            if [[ -z "$node_id" || "$node_id" == "null" ]]; then
                node_id=$(echo "$response_body" | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*\([0-9]\+\).*/\1/p' | head -1)
                echo "DEBUG: sed результат: '$node_id'" >&2
            fi
            
            # Метод 3: grep парсинг как fallback
            if [[ -z "$node_id" ]]; then
                node_id=$(echo "$response_body" | grep -o '"id"[[:space:]]*:[[:space:]]*[0-9]\+' | grep -o '[0-9]\+' | head -1)
                echo "DEBUG: grep результат: '$node_id'" >&2
            fi
            
            echo "DEBUG: Финальный ID: '$node_id'" >&2
            
            if [[ "$node_id" != "null" && -n "$node_id" && "$node_id" =~ ^[0-9]+$ ]]; then
                print_info "Узел успешно создан с ID: $node_id" >&2
                break
            fi
            
            # Если не удалось получить ID, попробуем найти созданный узел
            print_info "Ответ не содержит ID, проверяем список узлов..." >&2
            sleep 2
            
            local nodes_response=$(curl -s --connect-timeout 10 --max-time 30 \
                "$panel_url/api/nodes" \
                -H "Authorization: Bearer $admin_token" 2>/dev/null)
            
            if [[ $? -eq 0 && -n "$nodes_response" ]]; then
                print_info "Получен список узлов: ${nodes_response:0:200}$([ ${#nodes_response} -gt 200 ] && echo "...")" >&2
                
                # Найти узел по имени
                if [[ "$USE_JQ" == "true" ]]; then
                    node_id=$(echo "$nodes_response" | jq -r ".items[] | select(.name == \"$node_name\") | .id" 2>/dev/null | head -1)
                else
                    # Найти узел по имени используя простой парсинг
                    local node_data=$(echo "$nodes_response" | grep -o "\"name\":\"$node_name\"[^}]*" | head -1)
                    if [[ -n "$node_data" ]]; then
                        # Поиск ID в найденных данных узла
                        node_id=$(echo "$node_data" | grep -o "\"id\":[0-9]\+" | grep -o "[0-9]\+" | head -1)
                        # Если не нашли рядом с именем, ищем в начале объекта узла
                        if [[ -z "$node_id" ]]; then
                            local full_node_object=$(echo "$nodes_response" | grep -o "{[^}]*\"name\":\"$node_name\"[^}]*}" | head -1)
                            node_id=$(extract_json_value "$full_node_object" "id")
                        fi
                    fi
                fi
                
                print_info "ID найденного узла: '$node_id'" >&2
                
                if [[ "$node_id" != "null" && -n "$node_id" && "$node_id" =~ ^[0-9]+$ ]]; then
                    print_info "Найден созданный узел с ID: $node_id" >&2
                    break
                fi
            else
                print_warning "Не удалось получить список узлов для проверки" >&2
            fi
        fi
        
        print_warning "Попытка $attempt не удалась (HTTP: $http_code, Exit: $exit_code)" >&2
        if [[ -n "$response_body" ]]; then
            local short_response=$(echo "$response_body" | head -c 200)
            print_info "Ответ сервера: $short_response" >&2
        fi
        
        # Экспоненциальная задержка перед повтором
        if [[ $attempt -lt $max_attempts ]]; then
            local delay=$((2 ** attempt))
            print_info "Повтор через $delay секунд..." >&2
            sleep $delay
        fi
        
        ((attempt++))
    done
    
    if [[ -n "$node_id" && "$node_id" =~ ^[0-9]+$ ]]; then
        echo "$node_id"  # Это единственный stdout - возвращаемое значение
        print_ok >&2
        print_success "Узел '$node_name' зарегистрирован в панели (ID: $node_id)" >&2
        return 0
    fi
    
    print_fail >&2
    print_error "Не удалось создать узел в панели после $max_attempts попыток" >&2
    return 1
}

# Создать Dockerfile для WildosNode
create_wildosnode_dockerfile() {
    print_step "Создание Dockerfile для WildosNode"
    
    cat > "$INSTALL_DIR/Dockerfile" << EOF
FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Установка системных зависимостей
RUN apk add --no-cache curl unzip alpine-sdk libffi-dev wget

# Установка Xray
RUN wget https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip && \\
    unzip Xray-linux-64.zip && \\
    install -m 755 xray /usr/bin/xray && \\
    mkdir -p /usr/share/xray && \\
    install -m 644 geoip.dat /usr/share/xray/geoip.dat && \\
    install -m 644 geosite.dat /usr/share/xray/geosite.dat && \\
    rm -f Xray-linux-64.zip xray

# Установка Hysteria (получаем последнюю версию)
RUN HYSTERIA_VERSION=\$(wget -qO- https://api.github.com/repos/apernet/hysteria/releases/latest | grep '"tag_name"' | cut -d'"' -f4) && \\
    wget https://github.com/apernet/hysteria/releases/download/\$HYSTERIA_VERSION/hysteria-linux-amd64 -O /usr/bin/hysteria && \\
    chmod +x /usr/bin/hysteria

# Установка Sing-box (получаем последнюю версию)
RUN SINGBOX_VERSION=\$(wget -qO- https://api.github.com/repos/SagerNet/sing-box/releases/latest | grep '"tag_name"' | cut -d'"' -f4) && \\
    wget https://github.com/SagerNet/sing-box/releases/download/\$SINGBOX_VERSION/sing-box-\${SINGBOX_VERSION#v}-linux-amd64.tar.gz && \\
    tar -xzf sing-box-\${SINGBOX_VERSION#v}-linux-amd64.tar.gz && \\
    install -m 755 sing-box-\${SINGBOX_VERSION#v}-linux-amd64/sing-box /usr/bin/sing-box && \\
    rm -rf sing-box-*

# Копирование исходного кода
COPY wildosnode/ .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Очистка build dependencies
RUN apk del alpine-sdk libffi-dev curl unzip

# Создание директорий для данных
RUN mkdir -p /var/lib/wildosnode/configs /var/lib/wildosnode/ssl /var/lib/wildosnode/logs

# Экспорт портов
EXPOSE 62050

# Команда запуска
CMD ["python3", "wildosnode.py"]
EOF
    
    print_ok >&2
}

# Создать продакшен конфигурацию
create_production_config() {
    local node_id="$1"
    local panel_url="$2"
    local hostname="$3"
    local node_token="$4"
    local service_port="${5:-$DEFAULT_PORT}"  # Использовать переданный порт или стандартный
    
    print_step "Создание продакшен конфигурации"
    
    cat > "$DATA_DIR/.env" <<EOF
# WildosNode Production Configuration
# Generated on: $(date)

# Node Identity
NODE_ID=${node_id}
NODE_NAME=wildosnode-${hostname}
HOSTNAME=${hostname}

# Service Configuration  
SERVICE_ADDRESS=0.0.0.0
SERVICE_PORT=${service_port}

# Production Security
PRODUCTION_MODE=true
INSECURE=false
USE_SSL=true

# Panel Communication
PANEL_URL=${panel_url}
NODE_TOKEN=${node_token}

# SSL Configuration
SSL_CERT_PATH=${SSL_DIR}/node.cert
SSL_KEY_PATH=${SSL_DIR}/node.key
CA_CERT_PATH=${SSL_DIR}/ca.cert
SSL_CERT_FILE=${SSL_DIR}/node.cert
SSL_KEY_FILE=${SSL_DIR}/node.key
SSL_CLIENT_CERT_FILE=${SSL_DIR}/ca.cert

# Xray Configuration
XRAY_CONFIG_PATH=/app/xray_config.json

# Monitoring
ENABLE_HEALTH_CHECK=true
HEALTH_CHECK_INTERVAL=30
LOG_LEVEL=INFO

# Resource Limits
MAX_MEMORY=512m
MAX_CPU=1.0
DISK_USAGE_THRESHOLD=85
EOF
    
    print_ok >&2
}

# Создать продакшен Docker Compose
create_production_docker_compose() {
    local service_port="${1:-$DEFAULT_PORT}"  # Использовать переданный порт или стандартный
    
    print_step "Создание Docker Compose конфигурации (порт: $service_port)"
    
    mkdir -p "$COMPOSE_DIR"
    
    cat > "$DOCKER_COMPOSE_FILE" <<EOF
services:
  wildosnode:
    build: ${INSTALL_DIR}
    container_name: wildosnode-production
    restart: unless-stopped
    network_mode: host
    env_file:
      - ${DATA_DIR}/.env
    environment:
      - PYTHONUNBUFFERED=1
      - PRODUCTION_MODE=true
      - SSL_ENABLED=true
      - SSL_CLIENT_CERT_FILE=/var/lib/wildosnode/ssl/ca.cert
      - SSL_CERT_FILE=/var/lib/wildosnode/ssl/node.cert
      - SSL_KEY_FILE=/var/lib/wildosnode/ssl/node.key
      - XRAY_CONFIG_PATH=/app/xray_config.json
    volumes:
      - ${DATA_DIR}:/var/lib/wildosnode
      - ${SSL_DIR}:/etc/ssl/wildosnode:ro
    working_dir: /app
    command: ["python3", "wildosnode.py"]
    healthcheck:
      test: ["CMD", "python3", "-c", "import ssl,socket;s=ssl.create_default_context().wrap_socket(socket.socket());s.connect(('127.0.0.1',${service_port}));s.close()"]
      interval: 30s
      timeout: 5s
      retries: 2
      start_period: 45s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    security_opt:
      - no-new-privileges:true
EOF
    
    print_ok >&2
}


# Собрать и запустить продакшен сервис
start_production_service() {
    print_step "Сборка и запуск продакшен сервиса"
    
    cd "$COMPOSE_DIR"
    
    # Остановить существующие сервисы
    run_docker_compose -f "$DOCKER_COMPOSE_FILE" down 2>/dev/null || true
    
    # Собрать образ локально
    print_info "Сборка образа WildosNode..."
    if run_docker_compose -f "$DOCKER_COMPOSE_FILE" build --no-cache; then
        print_ok
        print_info "Образ успешно собран"
    else
        print_fail
        print_error "Не удалось собрать образ"
        exit 1
    fi
    
    # Запустить новый сервис
    print_info "Запуск сервиса..."
    run_docker_compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    # Проверить статус
    sleep 10
    if run_docker_compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
        print_ok
        print_success "Сервис успешно запущен"
    else
        print_fail
        print_error "Не удалось запустить сервис"
        run_docker_compose -f "$DOCKER_COMPOSE_FILE" logs --tail 20
        exit 1
    fi
}

# Показать статус продакшена
show_production_status() {
    local panel_url="$1"
    local node_id="$2"
    
    echo
    colorized_echo cyan "=== Статус продакшен установки ==="
    echo
    
    # Статус контейнера
    print_info "Статус Docker:"
    run_docker_compose -f "$DOCKER_COMPOSE_FILE" ps
    echo
    
    # Статус SSL
    print_info "SSL Сертификат:"
    if [[ -f "$SSL_DIR/node.cert" ]]; then
        local cert_info=$(openssl x509 -in "$SSL_DIR/node.cert" -noout -subject -dates 2>/dev/null)
        echo "$cert_info"
    else
        print_warning "SSL сертификат не найден"
    fi
    echo
    
    # Инструкции
    print_info "Полезные команды:"
    # Определяем какую команду показать пользователю
    local compose_cmd="docker compose"
    if ! docker compose version >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then
        compose_cmd="docker-compose"
    fi
    
    echo "  Логи:        $compose_cmd -f $DOCKER_COMPOSE_FILE logs -f"
    echo "  Рестарт:     $compose_cmd -f $DOCKER_COMPOSE_FILE restart"
    echo "  Статус:      $compose_cmd -f $DOCKER_COMPOSE_FILE ps"
    echo "  Остановка:   $compose_cmd -f $DOCKER_COMPOSE_FILE down"
    echo
    
    print_info "Конфигурация:"
    echo "  Node ID:     $node_id"
    echo "  Panel URL:   $panel_url"
    echo "  SSL Dir:     $SSL_DIR"
    echo "  Data Dir:    $DATA_DIR"
    echo
    
    print_success "Узел готов к работе в продакшен режиме!"
}

# ===============================================================================
# Helper Functions
# ===============================================================================

check_dependencies() {
    print_step "Проверка зависимостей"
    
    local missing_deps=()
    
    # Обязательные зависимости
    for cmd in docker curl jq openssl; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_fail
        print_error "Отсутствуют зависимости: ${missing_deps[*]}"
        print_info "Установите их и повторите попытку"
        exit 1
    fi
    
    print_ok
}

create_directories() {
    print_step "Создание структуры директорий"
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$SSL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$COMPOSE_DIR"
    mkdir -p "$LOG_DIR"
    
    # Установить права доступа
    chmod 755 "$INSTALL_DIR" "$DATA_DIR" "$CONFIG_DIR" "$COMPOSE_DIR" "$LOG_DIR"
    chmod 700 "$SSL_DIR"  # Только владелец может читать SSL
    
    print_ok
}

download_source_code() {
    print_step "Загрузка исходного кода"
    
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        cd "$INSTALL_DIR"
        git pull origin "$REPO_BRANCH" >/dev/null 2>&1
    else
        git clone -b "$REPO_BRANCH" "$REPO_URL" "$INSTALL_DIR" >/dev/null 2>&1
    fi
    
    print_ok
}

# ===============================================================================
# Menu System
# ===============================================================================

# Показать главное меню
show_main_menu() {
    clear
    colorized_echo cyan "╔════════════════════════════════════════════════════════════╗"
    colorized_echo cyan "║        WildosNode Management Script v$SCRIPT_VERSION              ║"
    colorized_echo cyan "║             Управление узлами WildosVPN                   ║"
    colorized_echo cyan "╚════════════════════════════════════════════════════════════╝"
    echo
    colorized_echo white "Выберите действие:"
    echo
    colorized_echo green "  1) Установка"   
    colorized_echo white "     Полная установка нового узла WildosNode"
    echo
    colorized_echo yellow "  2) Обновление"
    colorized_echo white "     Обновление существующего узла до последней версии"
    echo
    colorized_echo red "  3) Выход"
    echo
    colorized_echo cyan "════════════════════════════════════════════════════════════"
}

# Обработать выбор меню
handle_menu_choice() {
    local choice="$1"
    
    case "$choice" in
        "1")
            colorized_echo green "→ Запуск установки..."
            echo
            main_installation
            ;;
        "2")
            colorized_echo yellow "→ Запуск обновления..."
            echo
            update_wildosnode
            ;;
        "3")
            colorized_echo white "Выход из программы"
            exit 0
            ;;
        *)
            colorized_echo red "❌ Неверный выбор. Пожалуйста, выберите 1, 2 или 3."
            echo
            sleep 2
            return 1
            ;;
    esac
}

# Запустить интерактивное меню
run_interactive_menu() {
    while true; do
        show_main_menu
        
        # Запросить выбор у пользователя
        read -p "Введите номер действия (1-3): " user_choice
        echo
        
        # Обработать выбор
        if handle_menu_choice "$user_choice"; then
            # Если действие завершилось успешно, показать меню снова
            echo
            colorized_echo cyan "Нажмите Enter для возврата в главное меню..."
            read
        fi
    done
}

# ===============================================================================
# Main Installation Function
# ===============================================================================

# Переименованная основная функция установки
main_installation() {
    # Проверить root права
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт должен запускаться с правами root"
        exit 1
    fi
    
    # Заголовок
    clear
    colorized_echo cyan "╔════════════════════════════════════════════════════════════╗"
    colorized_echo cyan "║        WildosNode Production Installation v$SCRIPT_VERSION          ║"
    colorized_echo cyan "║             Secure Setup for External Servers             ║"
    colorized_echo cyan "╚════════════════════════════════════════════════════════════╝"
    echo
    
    # Сбор параметров для продакшена
    colorized_echo yellow "Настройка продакшен конфигурации:"
    echo
    
    # URL панели управления
    while true; do
        read -p "URL панели управления (например, https://panel.example.com): " PANEL_URL
        if [[ -n "$PANEL_URL" && "$PANEL_URL" =~ ^https?:// ]]; then
            break
        else
            print_error "Укажите корректный URL панели (http:// или https://)"
        fi
    done
    
    # Токен администратора
    while true; do
        read -s -p "Токен администратора панели: " ADMIN_TOKEN
        echo
        if [[ -n "$ADMIN_TOKEN" ]]; then
            break
        else
            print_error "Токен администратора обязателен"
        fi
    done
    
    # Имя узла
    DEFAULT_NODE_NAME="wildosnode-$(hostname)"
    read -p "Имя узла (по умолчанию $DEFAULT_NODE_NAME): " NODE_NAME
    NODE_NAME=${NODE_NAME:-$DEFAULT_NODE_NAME}
    
    # Hostname для SSL
    DEFAULT_HOSTNAME="$(hostname -f 2>/dev/null || hostname)"
    read -p "Hostname для SSL сертификата (по умолчанию $DEFAULT_HOSTNAME): " SSL_HOSTNAME
    SSL_HOSTNAME=${SSL_HOSTNAME:-$DEFAULT_HOSTNAME}
    
    echo
    colorized_echo green "Параметры продакшен установки:"
    echo "  Panel URL:    $PANEL_URL"
    echo "  Node Name:    $NODE_NAME"
    echo "  SSL Hostname: $SSL_HOSTNAME"
    echo
    
    read -p "Продолжить установку? (y/N): " CONFIRM
    if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
        print_info "Установка отменена"
        exit 0
    fi
    
    # Запуск установки
    install_production_node "$PANEL_URL" "$NODE_NAME" "$SSL_HOSTNAME" "$ADMIN_TOKEN"
}

# ===============================================================================
# Script Entry Point
# ===============================================================================

# Обработка аргументов командной строки  
case "${1:-}" in
    "update")
        # Прямой вызов обновления (для обратной совместимости)
        update_wildosnode
        ;;
    "install")
        # Прямой вызов установки (для обратной совместимости)
        main_installation
        ;;
    "menu" | "")
        # Запуск интерактивного меню (по умолчанию)
        run_interactive_menu
        ;;
    "--help" | "-h")
        # Показать справку
        colorized_echo cyan "WildosNode Management Script v$SCRIPT_VERSION"
        echo
        colorized_echo white "Использование:"
        echo "  $0                 - Запустить интерактивное меню (по умолчанию)"
        echo "  $0 menu            - Запустить интерактивное меню"
        echo "  $0 install         - Прямой запуск установки"
        echo "  $0 update          - Прямой запуск обновления"
        echo "  $0 --help          - Показать эту справку"
        echo
        exit 0
        ;;
    *)
        colorized_echo red "❌ Неверный аргумент: $1"
        colorized_echo white "Используйте $0 --help для справки"
        exit 1
        ;;
esac
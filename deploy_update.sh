#!/bin/bash

# Скрипт быстрого обновления кода на сервере
# Автор: AI Assistant
# Дата: 10 сентября 2025

set -e

echo "🔄 БЫСТРОЕ ОБНОВЛЕНИЕ КОДА"
echo "=========================="

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

# Проверяем наличие конфигурации
if [ ! -f "server_config.json" ]; then
    print_error "Файл server_config.json не найден"
    exit 1
fi

# Извлекаем параметры из конфигурации
HOST=$(grep -o '"host": "[^"]*"' server_config.json | cut -d'"' -f4)
USERNAME=$(grep -o '"username": "[^"]*"' server_config.json | cut -d'"' -f4)
SSH_KEY=$(grep -o '"ssh_key_path": "[^"]*"' server_config.json | cut -d'"' -f4)

print_info "Сервер: $HOST"
print_info "Пользователь: $USERNAME"

# Проверяем SSH ключ (расширяем ~)
SSH_KEY_EXPANDED="${SSH_KEY/#\~/$HOME}"
if [ ! -f "$SSH_KEY_EXPANDED" ]; then
    print_error "SSH ключ не найден: $SSH_KEY_EXPANDED"
    exit 1
fi
SSH_KEY="$SSH_KEY_EXPANDED"

# Функция для выполнения команд на сервере
run_remote() {
    local cmd="$1"
    local desc="$2"
    
    if [ -n "$desc" ]; then
        print_step "$desc"
    fi
    
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$USERNAME@$HOST" "$cmd"
    
    if [ $? -eq 0 ]; then
        if [ -n "$desc" ]; then
            print_status "$desc - успешно"
        fi
        return 0
    else
        if [ -n "$desc" ]; then
            print_error "$desc - ошибка"
        fi
        return 1
    fi
}

# Проверяем подключение к серверу
print_info "Проверяем подключение к серверу..."
if ! run_remote "echo 'Подключение успешно'" "Проверка подключения"; then
    print_error "Не удается подключиться к серверу"
    exit 1
fi

# Останавливаем сервис
print_info "Останавливаем сервис..."
run_remote "systemctl stop video-server" "Остановка сервиса"

# Создаем временный файл с исключениями для rsync
EXCLUDE_FILE=$(mktemp)
cat > "$EXCLUDE_FILE" << 'EOF'
# Конфигурационные файлы с секретными данными
server_config.json
.env
.env.local
.env.production

# Python кэш и временные файлы
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE файлы
.vscode/
.idea/
*.swp
*.swo
*~

# OS файлы
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Логи
*.log
logs/
app.log

# Загруженные файлы и результаты
uploads/
outputs/
temp/
tests/*.mp4
tests/*.avi
tests/*.mov

# База данных
*.db
*.sqlite
*.sqlite3

# Docker файлы
Dockerfile
docker-compose.yml
.dockerignore
docker/

# Backup файлы
backup/
*.bak
*.backup

# Временные файлы
tmp/
temp/
*.tmp

# Git файлы
.git/
.gitignore
.gitattributes

# Документация
*.md
!README.md

# Скрипты разработки
scripts/gpu_optimization_test.py
scripts/performance_test.py
scripts/quick_performance_test.py
scripts/simple_quality_test.py
scripts/test_quality.py
scripts/monitor_performance.py

# Конфигурационные файлы разработки
config_profiles.json
quality_profiles.json
performance_config.py

# Отчеты и анализ
*_REPORT.md
*_ANALYSIS.md
*_FIX_REPORT.md
*_GUIDE.md
*_SUCCESS_REPORT.md

# Тестовые видео файлы
*.mp4
*.avi
*.mov
*.mkv
*.wmv
*.flv
*.webm

# Временные конфигурации
server_setup_config.json
server_optimization_config.json
logging_config.json
start_server.sh

# Makefile
Makefile

# Скрипты развертывания
deploy*.sh
deploy*.py
EOF

# Копируем только измененные файлы
print_info "Копируем обновленный код..."
print_step "Исключаем лишние файлы при копировании"

rsync -avz --delete \
    --exclude-from="$EXCLUDE_FILE" \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" \
    ./ "$USERNAME@$HOST:/opt/video-server/"

if [ $? -eq 0 ]; then
    print_status "Код обновлен (с исключениями)"
else
    print_error "Ошибка обновления кода"
    rm -f "$EXCLUDE_FILE"
    exit 1
fi

# Удаляем временный файл
rm -f "$EXCLUDE_FILE"

# Устанавливаем права
print_info "Устанавливаем права на файлы..."
run_remote "chmod +x /opt/video-server/scripts/*.py" "Установка прав"

# Обновляем зависимости (если изменились)
print_info "Проверяем зависимости..."
run_remote "cd /opt/video-server && source venv/bin/activate && pip install -r requirements_server.txt" "Обновление зависимостей"

# Запускаем сервис
print_info "Запускаем сервис..."
run_remote "systemctl start video-server && sleep 3" "Запуск сервиса"

# Проверяем статус сервиса
print_info "Проверяем статус сервиса..."
STATUS=$(run_remote "systemctl status video-server --no-pager" "")
echo "$STATUS"

# Проверяем API
print_info "Проверяем API..."
API_RESPONSE=$(run_remote "curl -s http://localhost/health" "")
if [ $? -eq 0 ]; then
    print_status "API работает: $API_RESPONSE"
else
    print_warning "API не отвечает"
fi

# Показываем информацию об обновлении
echo ""
echo "🎉 ОБНОВЛЕНИЕ КОДА ЗАВЕРШЕНО!"
echo "============================="
echo "🌐 Сервер: $HOST"
echo "🔗 API: http://$HOST:8080"
echo "📚 Документация: http://$HOST:8080/docs"
echo "============================="

print_status "Код успешно обновлен!"

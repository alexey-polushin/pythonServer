#!/bin/bash

# Оптимизированный скрипт развертывания с исключением лишних файлов
# Автор: AI Assistant
# Дата: 10 сентября 2025

set -e

echo "🚀 ОПТИМИЗИРОВАННОЕ РАЗВЕРТЫВАНИЕ"
echo "=================================="

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
print_info "SSH ключ: $SSH_KEY"

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

# Проверяем Python
print_info "Проверяем Python на сервере..."
PYTHON_VERSION=$(run_remote "python3 --version" "")
if [ $? -eq 0 ]; then
    print_status "Python найден: $PYTHON_VERSION"
else
    print_error "Python3 не найден на сервере"
    exit 1
fi

# Устанавливаем системные зависимости
print_info "Устанавливаем системные зависимости..."
run_remote "apt update && apt install -y python3-pip python3-venv ffmpeg build-essential libssl-dev libffi-dev git rsync" "Установка зависимостей"

# Создаем директорию приложения
print_info "Создаем директорию приложения..."
run_remote "mkdir -p /opt/video-server" "Создание директории"

# Копируем только необходимые файлы с исключениями
print_info "Копируем только необходимые файлы..."
print_step "Исключаем лишние файлы при копировании"

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

# Документация (оставляем только README)
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

# Копируем файлы с исключениями
rsync -avz --delete \
    --exclude-from="$EXCLUDE_FILE" \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" \
    ./ "$USERNAME@$HOST:/opt/video-server/"

if [ $? -eq 0 ]; then
    print_status "Файлы скопированы (с исключениями)"
else
    print_error "Ошибка копирования файлов"
    rm -f "$EXCLUDE_FILE"
    exit 1
fi

# Удаляем временный файл
rm -f "$EXCLUDE_FILE"

# Устанавливаем права
print_info "Устанавливаем права на файлы..."
run_remote "chmod +x /opt/video-server/scripts/*.py" "Установка прав"

# Настраиваем приложение
print_info "Настраиваем приложение..."
run_remote "cd /opt/video-server && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements_server.txt" "Установка Python зависимостей"

# Запускаем автоматическую настройку
print_info "Запускаем автоматическую настройку..."
run_remote "cd /opt/video-server && source venv/bin/activate && python3 scripts/auto_setup_server.py --skip-deps" "Автоматическая настройка"

# Оптимизируем настройки
print_info "Оптимизируем настройки производительности..."
run_remote "cd /opt/video-server && source venv/bin/activate && python3 scripts/remote_server_optimizer.py --skip-test" "Оптимизация настроек"

# Проверяем применение настроек
print_info "Проверяем применение настроек..."
run_remote "cd /opt/video-server && source venv/bin/activate && python3 -c 'from src.dive_color_corrector.mobile_correct import get_performance_info; import json; print(\"Настройки:\", json.dumps(get_performance_info(), indent=2))'" "Проверка настроек"

# Создаем systemd сервис
print_info "Создаем systemd сервис..."
run_remote "cat > /etc/systemd/system/video-server.service << 'EOF'
[Unit]
Description=Video Processing Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/video-server
ExecStart=/opt/video-server/venv/bin/python app.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/video-server/src

[Install]
WantedBy=multi-user.target
EOF" "Создание systemd сервиса"

# Включаем и запускаем сервис
print_info "Включаем и запускаем сервис..."
run_remote "systemctl daemon-reload && systemctl enable video-server && systemctl start video-server" "Запуск сервиса"

# Перезапускаем сервис для применения настроек
print_info "Перезапускаем сервис для применения настроек..."
run_remote "systemctl restart video-server && sleep 3" "Перезапуск сервиса"

# Устанавливаем и настраиваем nginx
print_info "Устанавливаем и настраиваем nginx..."
run_remote "apt install -y nginx" "Установка nginx"

# Создаем конфигурацию nginx
print_info "Создаем конфигурацию nginx..."
run_remote "cat > /etc/nginx/sites-available/video-server << 'EOF'
# Настройки для больших файлов
client_max_body_size 500M;
client_body_timeout 300s;
client_header_timeout 300s;
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;
send_timeout 300s;

upstream video_api {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://video_api;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        
        # Настройки для больших файлов
        proxy_request_buffering off;
        proxy_buffering off;
        proxy_max_temp_file_size 0;
    }

    location /health {
        proxy_pass http://video_api/health;
        access_log off;
    }
}
EOF" "Создание конфигурации nginx"

# Активируем конфигурацию nginx
print_info "Активируем конфигурацию nginx..."
run_remote "ln -sf /etc/nginx/sites-available/video-server /etc/nginx/sites-enabled/ && rm -f /etc/nginx/sites-enabled/default && nginx -t" "Активация nginx"

# Запускаем nginx
print_info "Запускаем nginx..."
run_remote "systemctl start nginx && systemctl enable nginx" "Запуск nginx"

# Настраиваем файрвол
print_info "Настраиваем файрвол..."
run_remote "ufw allow 22/tcp && ufw allow 80/tcp && ufw --force enable" "Настройка файрвола"

# Проверяем статус сервиса
print_info "Проверяем статус сервиса..."
STATUS=$(run_remote "systemctl status video-server --no-pager" "")
echo "$STATUS"

# Финальная проверка настроек
print_info "Финальная проверка настроек..."
run_remote "cd /opt/video-server && source venv/bin/activate && python3 -c 'from src.dive_color_corrector.mobile_correct import get_performance_info; import json; info = get_performance_info(); print(f\"✅ Настройки применены: batch={info[\"batch_size\"]}, proc={info[\"max_processes\"]}, quality={info[\"video_quality\"]}%\")'" "Финальная проверка"

# Проверяем API
print_info "Проверяем API..."
API_RESPONSE=$(run_remote "curl -s http://localhost/health" "")
if [ $? -eq 0 ]; then
    print_status "API работает: $API_RESPONSE"
else
    print_warning "API не отвечает"
fi

# Проверяем настройки больших файлов
print_info "Проверяем настройки больших файлов..."
NGINX_CONFIG=$(run_remote "grep -c 'client_max_body_size 500M' /etc/nginx/sites-available/video-server" "")
if [ "$NGINX_CONFIG" -gt 0 ]; then
    print_status "Nginx настроен для файлов до 500MB"
else
    print_warning "Nginx не настроен для больших файлов"
fi

# Показываем информацию о развертывании
echo ""
echo "🎉 ОПТИМИЗИРОВАННОЕ РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo "============================================="
echo "🌐 Сервер: $HOST"
echo "🔗 API: http://$HOST"
echo "📚 Документация: http://$HOST/docs"
echo ""
echo "📋 Команды управления:"
echo "  ssh -i $SSH_KEY $USERNAME@$HOST"
echo "  systemctl status video-server"
echo "  systemctl restart video-server"
echo "  systemctl stop video-server"
echo ""
echo "📊 Мониторинг:"
echo "  cd /opt/video-server"
echo "  source venv/bin/activate"
echo "  python scripts/performance_monitor.py"
echo ""
echo "⚙️ Оптимизация:"
echo "  python scripts/remote_server_optimizer.py"
echo "  python scripts/set_quality_profile.py list"
echo "============================================="

print_status "Оптимизированное развертывание успешно завершено!"

#!/bin/bash

# Универсальный скрипт развертывания Python API Server
# Подходит для Debian/Ubuntu
set -e

echo "🚀 Начинаем развертывание Python API Server с поддержкой обработки видео..."
echo "📋 Обнаруженная ОС: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Debian/Ubuntu")"

# Обновление системы
echo "📦 Обновляем систему..."
apt update && apt upgrade -y

# Установка необходимых пакетов для обработки видео
echo "🎥 Устанавливаем зависимости для обработки видео..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    gfortran \
    wget \
    curl \
    git \
    unzip \
    ffmpeg \
    rsync \
    sshpass

# Установка Docker
echo "🐳 Устанавливаем Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker установлен"
else
    echo "✅ Docker уже установлен"
fi

# Установка Docker Compose
echo "🔧 Устанавливаем Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose установлен"
else
    echo "✅ Docker Compose уже установлен"
fi

# Настройка файрвола (с проверкой наличия)
echo "🔥 Настраиваем файрвол..."
if command -v ufw &> /dev/null; then
    ufw --force enable
    ufw allow 22
    ufw allow 80
    ufw allow 443
    echo "✅ Файрвол настроен"
else
    echo "⚠️ ufw не найден, устанавливаем..."
    apt install -y ufw
    ufw --force enable
    ufw allow 22
    ufw allow 80
    ufw allow 443
    echo "✅ Файрвол установлен и настроен"
fi

# Создание директории для проекта
echo "📁 Создаем директорию проекта..."
mkdir -p /opt/dive-color-corrector
cd /opt/dive-color-corrector

# Создание .env файла если не существует
if [ ! -f .env ]; then
    echo "⚙️ Создаем .env файл..."
    cat > .env << EOF
HOST=0.0.0.0
PORT=8080
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
API_TOKEN=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///./app.db
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO
UPLOAD_DIR=/app/uploads
OUTPUT_DIR=/app/outputs
MAX_FILE_SIZE=500MB
EOF
    echo "✅ .env файл создан"
else
    echo "✅ .env файл уже существует"
fi

# Создание директорий для загрузок и выходных файлов
echo "📂 Создаем директории для файлов..."
mkdir -p uploads outputs logs

# Создание systemd сервиса для автоматического запуска
echo "🔧 Создаем systemd сервис..."
cat > /etc/systemd/system/dive-color-corrector.service << EOF
[Unit]
Description=Python API Server with Dive Color Corrector
After=network.target

[Service]
User=root
WorkingDirectory=/opt/dive-color-corrector
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd и включение сервиса
systemctl daemon-reload
systemctl enable dive-color-corrector.service

# Создание скрипта для обновления
echo "📝 Создаем скрипт обновления..."
cat > /opt/dive-color-corrector/update.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Обновляем Python API Server..."

# Остановка сервиса
systemctl stop dive-color-corrector.service

# Создание бэкапа
if [ -d "backup" ]; then
    rm -rf backup
fi
mkdir backup
cp -r . backup/ 2>/dev/null || true

# Остановка контейнеров
docker-compose down 2>/dev/null || true

# Обновление кода (если используется git)
if [ -d ".git" ]; then
    git pull origin main
fi

# Пересборка и запуск
docker-compose up -d --build

# Запуск сервиса
systemctl start dive-color-corrector.service

echo "✅ Обновление завершено!"
EOF

chmod +x /opt/dive-color-corrector/update.sh

# Создание скрипта для мониторинга
echo "📊 Создаем скрипт мониторинга..."
cat > /opt/dive-color-corrector/monitor.sh << 'EOF'
#!/bin/bash

echo "📊 Статус Python API Server:"
echo "================================"

# Статус systemd сервиса
echo "🔧 Systemd сервис:"
systemctl status dive-color-corrector.service --no-pager -l

echo ""
echo "🐳 Docker контейнеры:"
docker-compose ps

echo ""
echo "💾 Использование диска:"
df -h /opt/dive-color-corrector

echo ""
echo "🧠 Использование памяти:"
free -h

echo ""
echo "📁 Размер директорий:"
du -sh uploads outputs logs 2>/dev/null || echo "Директории не найдены"

echo ""
echo "🌐 Проверка доступности API:"
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ API доступен"
else
    echo "❌ API недоступен"
fi
EOF

chmod +x /opt/dive-color-corrector/monitor.sh

# Создание скрипта для очистки диска (мягкая версия)
echo "🧹 Создаем скрипт очистки диска..."
cat > /opt/disk_cleanup.sh << 'EOF'
#!/bin/bash

echo "🧹 Начинаем мягкую очистку диска..."
echo "Дата: $(date)"
echo

echo "📊 Состояние диска ДО очистки:"
df -h /
echo

echo "🐳 Очищаем неиспользуемые Docker образы..."
docker image prune -f
echo

echo "📦 Очищаем APT кэш..."
apt clean
apt autoremove -y
echo

echo "📝 Очищаем логи (старше 7 дней)..."
journalctl --vacuum-time=7d
echo

echo "🗑️ Очищаем временные файлы (старше 3 дней)..."
find /tmp -type f -atime +3 -delete 2>/dev/null || true
find /var/tmp -type f -atime +3 -delete 2>/dev/null || true
echo

echo "📊 Состояние диска ПОСЛЕ очистки:"
df -h /
echo

echo "✅ Мягкая очистка завершена!"
EOF

chmod +x /opt/disk_cleanup.sh

# Создание скрипта мониторинга диска
echo "📊 Создаем скрипт мониторинга диска..."
cat > /opt/check_disk.sh << 'EOF'
#!/bin/bash

echo "📊 Мониторинг диска:"
echo "Дата: $(date)"
echo

echo "💾 Использование диска:"
df -h /
echo

echo "🐳 Docker:"
docker system df
echo

echo "📦 Топ директории:"
du -sh /var/* 2>/dev/null | sort -hr | head -5
echo

echo "🧠 Память:"
free -h
echo

echo "📈 Нагрузка:"
uptime
EOF

chmod +x /opt/check_disk.sh

# Настройка автоматической очистки диска через cron (еженедельно)
echo "⏰ Настраиваем еженедельную очистку диска..."
echo "0 3 * * 0 /opt/disk_cleanup.sh >> /var/log/disk_cleanup.log 2>&1" | crontab -

echo "🎉 Настройка системы завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Скопируйте файлы проекта в /opt/dive-color-corrector/"
echo "2. Запустите: systemctl start dive-color-corrector.service"
echo "3. Проверьте статус: /opt/dive-color-corrector/monitor.sh"
echo ""
echo "🔧 Полезные команды:"
echo "  systemctl status dive-color-corrector.service  # Статус сервиса"
echo "  systemctl start dive-color-corrector.service   # Запуск сервиса"
echo "  systemctl stop dive-color-corrector.service    # Остановка сервиса"
echo "  systemctl restart dive-color-corrector.service # Перезапуск сервиса"
echo "  /opt/dive-color-corrector/monitor.sh           # Мониторинг API"
echo "  /opt/dive-color-corrector/update.sh            # Обновление"
echo "  /opt/disk_cleanup.sh                        # Мягкая очистка диска"
echo "  /opt/check_disk.sh                          # Мониторинг диска"
echo ""
echo "🌐 После запуска API будет доступен по адресу: http://$(curl -s ifconfig.me)"
echo "📚 Документация API: http://$(curl -s ifconfig.me)/docs"
echo "📱 Мобильный API: http://$(curl -s ifconfig.me)/api/mobile/status"
echo ""
echo "✨ Особенности версии:"
echo "  🚀 Подходит для Debian и Ubuntu"
echo "  🧹 Мягкая очистка диска (еженедельно)"
echo "  📊 Полный мониторинг системы"
echo "  🐳 Запуск всех сервисов (API, Redis, Nginx)"
echo "  ⚠️  API работает без авторизации для упрощения использования"

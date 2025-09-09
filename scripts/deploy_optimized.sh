#!/bin/bash

# Оптимизированный скрипт автоматического развертывания на Debian VDS
# Включает все улучшения: оптимизация памяти, очистка диска, автоматическая очистка файлов
set -e

echo "🚀 Начинаем оптимизированное развертывание Python API Server с поддержкой обработки видео на Debian..."

# Обновление системы
echo "📦 Обновляем систему..."
apt update && apt upgrade -y

# Установка необходимых пакетов для обработки видео (без GUI)
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
    rsync

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

# Настройка файрвола (если ufw доступен)
echo "🔥 Настраиваем файрвол..."
if command -v ufw &> /dev/null; then
    ufw --force enable
    ufw allow 22
    ufw allow 80
    ufw allow 443
    ufw allow 8000
    echo "✅ Файрвол настроен"
else
    echo "⚠️ ufw не найден, пропускаем настройку файрвола"
fi

# Создание директории для проекта
echo "📁 Создаем директорию проекта..."
mkdir -p /opt/python-api-server
cd /opt/python-api-server

# Создание .env файла если не существует
if [ ! -f .env ]; then
    echo "⚙️ Создаем .env файл..."
    cat > .env << EOF
HOST=0.0.0.0
PORT=8000
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
cat > /etc/systemd/system/python-api-server.service << EOF
[Unit]
Description=Python API Server with Dive Color Corrector
After=network.target

[Service]
User=root
WorkingDirectory=/opt/python-api-server
ExecStart=/usr/local/bin/docker-compose up -d api redis
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd и включение сервиса
systemctl daemon-reload
systemctl enable python-api-server.service

# Создание скрипта для обновления
echo "📝 Создаем скрипт обновления..."
cat > /opt/python-api-server/update.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Обновляем Python API Server..."

# Остановка сервиса
systemctl stop python-api-server.service

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
docker-compose up -d --build api redis

# Запуск сервиса
systemctl start python-api-server.service

echo "✅ Обновление завершено!"
EOF

chmod +x /opt/python-api-server/update.sh

# Создание скрипта для мониторинга
echo "📊 Создаем скрипт мониторинга..."
cat > /opt/python-api-server/monitor.sh << 'EOF'
#!/bin/bash

echo "📊 Статус Python API Server:"
echo "================================"

# Статус systemd сервиса
echo "🔧 Systemd сервис:"
systemctl status python-api-server.service --no-pager -l

echo ""
echo "🐳 Docker контейнеры:"
docker-compose ps

echo ""
echo "💾 Использование диска:"
df -h /opt/python-api-server

echo ""
echo "🧠 Использование памяти:"
free -h

echo ""
echo "📁 Размер директорий:"
du -sh uploads outputs logs 2>/dev/null || echo "Директории не найдены"

echo ""
echo "🌐 Проверка доступности API:"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API доступен"
else
    echo "❌ API недоступен"
fi
EOF

chmod +x /opt/python-api-server/monitor.sh

# Создание скрипта для очистки диска
echo "🧹 Создаем скрипт очистки диска..."
cat > /opt/disk_cleanup.sh << 'EOF'
#!/bin/bash

echo "🧹 Начинаем очистку диска..."
echo "Дата: $(date)"
echo

echo "📊 Состояние диска ДО очистки:"
df -h /
echo

echo "🐳 Очищаем Docker..."
docker system prune -a --volumes -f
echo

echo "📦 Очищаем APT кэш..."
apt clean
apt autoremove -y
echo

echo "📝 Очищаем логи (старше 1 дня)..."
journalctl --vacuum-time=1d
echo

echo "🗑️ Очищаем временные файлы..."
rm -rf /tmp/*
rm -rf /var/tmp/*
echo

echo "📊 Состояние диска ПОСЛЕ очистки:"
df -h /
echo

echo "✅ Очистка завершена!"
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

# Настройка автоматической очистки диска через cron
echo "⏰ Настраиваем автоматическую очистку диска..."
echo "0 2 * * * /opt/disk_cleanup.sh >> /var/log/disk_cleanup.log 2>&1" | crontab -

# Выполняем первоначальную очистку
echo "🧹 Выполняем первоначальную очистку системы..."
/opt/disk_cleanup.sh

echo "🎉 Оптимизированная настройка системы завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Скопируйте файлы проекта в /opt/python-api-server/"
echo "2. Запустите: systemctl start python-api-server.service"
echo "3. Проверьте статус: /opt/python-api-server/monitor.sh"
echo ""
echo "🔧 Полезные команды:"
echo "  systemctl status python-api-server.service  # Статус сервиса"
echo "  systemctl start python-api-server.service   # Запуск сервиса"
echo "  systemctl stop python-api-server.service    # Остановка сервиса"
echo "  systemctl restart python-api-server.service # Перезапуск сервиса"
echo "  /opt/python-api-server/monitor.sh           # Мониторинг API"
echo "  /opt/python-api-server/update.sh            # Обновление"
echo "  /opt/disk_cleanup.sh                        # Очистка диска"
echo "  /opt/check_disk.sh                          # Мониторинг диска"
echo ""
echo "🌐 После запуска API будет доступен по адресу: http://$(curl -s ifconfig.me):8000"
echo "📚 Документация API: http://$(curl -s ifconfig.me):8000/docs"
echo "📱 Мобильный API: http://$(curl -s ifconfig.me):8000/api/mobile/status"
echo ""
echo "✨ Особенности оптимизированной версии:"
echo "  🚀 Оптимизированные настройки Gunicorn (2 воркера, таймаут 300с)"
echo "  🧹 Автоматическая очистка старых файлов при загрузке новых"
echo "  💾 Ежедневная автоматическая очистка диска (2:00 ночи)"
echo "  📊 Скрипты мониторинга диска и памяти"
echo "  🐳 Запуск только API и Redis (без nginx для экономии ресурсов)"
echo "  ⚠️  API работает без авторизации для упрощения использования"

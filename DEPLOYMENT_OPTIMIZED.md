# 🚀 Оптимизированное развертывание Python API Server

## 📋 Обзор

Этот документ описывает оптимизированное развертывание Python API Server с поддержкой обработки видео на Debian VDS. Включает все улучшения для стабильной работы на серверах с ограниченными ресурсами.

## ✨ Особенности оптимизированной версии

### 🚀 Производительность
- **Оптимизированные настройки Gunicorn**: 2 воркера, таймаут 300с, preload
- **Ограничения памяти**: max-requests 100, worker-connections 1000
- **Запуск только API и Redis**: без nginx для экономии ресурсов

### 🧹 Автоматическая очистка
- **Автоматическая очистка файлов**: при загрузке новых файлов удаляются старые
- **Ежедневная очистка диска**: автоматически в 2:00 ночи через cron
- **Очистка Docker**: удаление неиспользуемых образов и кэша
- **Очистка APT**: удаление кэша пакетов и неиспользуемых пакетов

### 📊 Мониторинг
- **Скрипты мониторинга**: диска, памяти, API статуса
- **Логирование**: все операции очистки записываются в логи
- **Health checks**: автоматическая проверка состояния API

## 🛠️ Требования

- **ОС**: Debian 11+ (Bullseye) или Ubuntu 20.04+
- **RAM**: минимум 512MB, рекомендуется 1GB+
- **Диск**: минимум 2GB свободного места
- **Сеть**: открытые порты 22 (SSH), 8000 (API)

## 📦 Быстрое развертывание

### 1. Загрузка скрипта
```bash
# Скачайте скрипт развертывания
wget https://raw.githubusercontent.com/your-repo/pythonServer/main/scripts/deploy_optimized.sh
chmod +x deploy_optimized.sh
```

### 2. Запуск развертывания
```bash
# Запустите скрипт развертывания
sudo ./deploy_optimized.sh
```

### 3. Копирование файлов проекта
```bash
# Скопируйте файлы проекта в директорию сервера
scp -r . root@your-server:/opt/python-api-server/
```

### 4. Запуск сервиса
```bash
# Запустите API сервер
sudo systemctl start python-api-server.service

# Проверьте статус
sudo systemctl status python-api-server.service
```

## 🔧 Управление сервисом

### Основные команды
```bash
# Статус сервиса
sudo systemctl status python-api-server.service

# Запуск сервиса
sudo systemctl start python-api-server.service

# Остановка сервиса
sudo systemctl stop python-api-server.service

# Перезапуск сервиса
sudo systemctl restart python-api-server.service
```

### Мониторинг
```bash
# Мониторинг API
/opt/python-api-server/monitor.sh

# Мониторинг диска
/opt/check_disk.sh

# Проверка Docker
docker system df
```

## 🧹 Очистка и обслуживание

### Ручная очистка
```bash
# Очистка диска
/opt/disk_cleanup.sh

# Очистка только Docker
docker system prune -a --volumes -f

# Очистка APT кэша
apt clean && apt autoremove -y
```

### Автоматическая очистка
- **Ежедневно в 2:00**: автоматическая очистка диска
- **При загрузке файлов**: автоматическая очистка старых файлов
- **Логи очистки**: `/var/log/disk_cleanup.log`

## 📊 Мониторинг ресурсов

### Проверка диска
```bash
# Использование диска
df -h /

# Топ директории по размеру
du -sh /var/* | sort -hr | head -10

# Размер Docker
docker system df
```

### Проверка памяти
```bash
# Использование памяти
free -h

# Топ процессы по памяти
ps aux --sort=-%mem | head -10

# Статус контейнеров
docker stats --no-stream
```

## 🌐 API Endpoints

### Основные endpoints
- **Health Check**: `GET /health`
- **API Status**: `GET /api/mobile/status`
- **Обработка изображений**: `POST /api/mobile/process/image`
- **Обработка видео**: `POST /api/mobile/process/video`
- **Список файлов**: `GET /api/mobile/files`
- **Скачивание файлов**: `GET /api/download/{filename}`

### Документация
- **Swagger UI**: `http://your-server:8000/docs`
- **ReDoc**: `http://your-server:8000/redoc`

## ⚠️ Важные особенности

### Без авторизации
- API работает без авторизации для упрощения использования
- Подходит для внутренних проектов и тестирования
- Для продакшена рекомендуется добавить авторизацию

### Ограничения ресурсов
- **Максимальный размер файла**: 50MB (рекомендуется)
- **Таймаут обработки**: 5 минут
- **Обработка по очереди**: не параллельно для экономии памяти

### Автоматическая очистка файлов
- При загрузке нового файла автоматически удаляются все старые
- Информация о количестве очищенных файлов в ответе API
- Логирование операций очистки

## 🚨 Устранение неполадок

### Проблемы с памятью
```bash
# Проверка использования памяти
free -h
docker stats --no-stream

# Очистка Docker
docker system prune -a --volumes -f

# Перезапуск сервиса
sudo systemctl restart python-api-server.service
```

### Проблемы с диском
```bash
# Проверка места на диске
df -h /

# Очистка диска
/opt/disk_cleanup.sh

# Проверка логов очистки
tail -f /var/log/disk_cleanup.log
```

### Проблемы с API
```bash
# Проверка статуса сервиса
sudo systemctl status python-api-server.service

# Проверка логов
sudo journalctl -u python-api-server.service -f

# Проверка контейнеров
docker-compose ps
docker-compose logs api
```

## 📝 Логи и мониторинг

### Логи системы
- **Systemd**: `sudo journalctl -u python-api-server.service`
- **Docker**: `docker-compose logs api`
- **Очистка**: `/var/log/disk_cleanup.log`

### Мониторинг в реальном времени
```bash
# Логи API в реальном времени
docker-compose logs -f api

# Мониторинг ресурсов
watch -n 5 '/opt/check_disk.sh'
```

## 🔄 Обновление

### Обновление кода
```bash
# Использование скрипта обновления
/opt/python-api-server/update.sh

# Ручное обновление
sudo systemctl stop python-api-server.service
# Обновить код
sudo systemctl start python-api-server.service
```

### Обновление системы
```bash
# Обновление пакетов
apt update && apt upgrade -y

# Очистка после обновления
/opt/disk_cleanup.sh
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u python-api-server.service`
2. Проверьте ресурсы: `/opt/check_disk.sh`
3. Выполните очистку: `/opt/disk_cleanup.sh`
4. Перезапустите сервис: `sudo systemctl restart python-api-server.service`

---

**🎯 Оптимизированная версия готова к работе на серверах с ограниченными ресурсами!**

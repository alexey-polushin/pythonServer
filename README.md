# Python API Server с обработкой видео

Оптимизированный Python API сервер на FastAPI для обработки изображений и видео с автоматической очисткой файлов.

## 🚀 Возможности

- **Обработка изображений и видео** с помощью dive-color-corrector
- **Автоматическая очистка файлов** при загрузке новых
- **Оптимизированные настройки** для серверов с ограниченными ресурсами
- **Автоматическая очистка диска** каждый день
- **Мониторинг ресурсов** (диск, память, API)
- **Без авторизации** для упрощения использования
- **Docker контейнеризация** с оптимизированными настройками

## 🛠 Быстрое развертывание

### Настройка конфигурации

1. **Создайте конфиг из примера:**
```bash
cp server_config.example.json server_config.json
```

2. **Отредактируйте данные сервера:**
```bash
nano server_config.json
```

> ⚠️ **Безопасность**: Файл `server_config.json` содержит конфиденциальные данные и исключен из git. См. [SECURITY.md](SECURITY.md) для подробностей.

📋 **Подробные инструкции:** [CONFIG_SETUP.md](CONFIG_SETUP.md)

### Автоматическое развертывание на Debian

1. **Скачайте и запустите скрипт:**
```bash
wget https://raw.githubusercontent.com/your-repo/pythonServer/main/scripts/deploy_optimized.sh
chmod +x deploy_optimized.sh
sudo ./deploy_optimized.sh
```

2. **Скопируйте файлы проекта:**
```bash
scp -r . root@your-server:/opt/python-api-server/
```

3. **Запустите сервис:**
```bash
sudo systemctl start python-api-server.service
```

### Локальная разработка

```bash
pip install -r src/requirements.txt
python app.py
```

Сервер будет доступен по адресу: http://localhost:8000

## 📚 API Endpoints

### Основные
- `GET /health` - Проверка работоспособности
- `GET /docs` - Документация API

### Мобильный API (без авторизации)
- `GET /api/mobile/status` - Статус API
- `GET /api/mobile/health` - Проверка здоровья
- `POST /api/mobile/process/image` - Обработка изображения
- `POST /api/mobile/process/video` - Обработка видео
- `GET /api/mobile/files` - Список файлов
- `GET /api/download/{filename}` - Скачивание файла

## 🔧 Управление сервисом

### Основные команды
```bash
# Статус сервиса
sudo systemctl status python-api-server.service

# Запуск/остановка/перезапуск
sudo systemctl start python-api-server.service
sudo systemctl stop python-api-server.service
sudo systemctl restart python-api-server.service
```

### Мониторинг
```bash
# Мониторинг API
/opt/python-api-server/monitor.sh

# Мониторинг диска
/opt/check_disk.sh

# Очистка диска
/opt/disk_cleanup.sh
```

## ⚠️ Важные особенности

- **API работает без авторизации** для упрощения использования
- **Автоматическая очистка файлов** при загрузке новых
- **Ограничения**: максимальный размер файла 50MB
- **Обработка по очереди** (не параллельно) для экономии ресурсов
- **Автоматическая очистка диска** каждый день в 2:00

## 📊 Мониторинг

- **Health check:** `curl http://your-server:8000/health`
- **Логи:** `docker-compose logs -f api`
- **Статус API:** `curl http://your-server:8000/api/mobile/status`

## 📚 Документация

- **Подробное развертывание:** [DEPLOYMENT_OPTIMIZED.md](DEPLOYMENT_OPTIMIZED.md)
- **Устранение проблем:** [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md)
- **Быстрое развертывание:** [QUICK_DEPLOY.md](QUICK_DEPLOY.md)
- **Безопасность:** [SECURITY.md](SECURITY.md)
- **История изменений:** [CHANGELOG.md](CHANGELOG.md)
- **API документация:** http://your-server:8000/docs

## 📝 Лицензия

MIT License

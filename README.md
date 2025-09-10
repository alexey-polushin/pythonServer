# Python API Server с обработкой видео

Универсальный Python API сервер на FastAPI для обработки изображений и видео с автоматической очисткой файлов.

## 🚀 Возможности

- **Обработка изображений и видео** с коррекцией цветов для подводной съемки
- **Автоматическая очистка файлов** при загрузке новых
- **Универсальные настройки** для Debian/Ubuntu
- **Мягкая очистка диска** еженедельно
- **Мониторинг ресурсов** (диск, память, API)
- **Docker контейнеризация** с полным набором сервисов

## 📋 Системные требования

- **ОС**: Debian 10+ или Ubuntu 18.04+
- **RAM**: минимум 2GB (рекомендуется 4GB+)
- **Диск**: минимум 10GB свободного места
- **CPU**: 2+ ядра
- **Сеть**: доступ к интернету для установки зависимостей

## 🛠 Быстрое развертывание

### Настройка конфигурации

1. **Создайте конфигурацию из шаблона:**
```bash
cp server_config.example.json server_config.json
```

2. **Отредактируйте данные сервера:**
```bash
nano server_config.json
```

**Основные параметры для изменения:**
- `server.host` - IP адрес или домен вашего сервера
- `server.username` - имя пользователя для SSH (обычно `root`)
- `server.auth_method` - метод аутентификации: `"password"` или `"key"`
- `server.password` - пароль для SSH подключения (если используется `auth_method: "password"`)
- `server.ssh_key_path` - путь к приватному SSH ключу (если используется `auth_method: "key"`)

**Примеры конфигурации:**

**Аутентификация по паролю:**
```json
{
  "server": {
    "host": "192.168.1.100",
    "username": "root",
    "auth_method": "password",
    "password": "your-password"
  }
}
```

**Аутентификация по SSH ключу:**
```json
{
  "server": {
    "host": "192.168.1.100",
    "username": "root",
    "auth_method": "key",
    "ssh_key_path": "/home/user/.ssh/id_rsa"
  }
}
```

> ⚠️ **Безопасность**: Файл `server_config.json` содержит конфиденциальные данные и исключен из git.

### Автоматическое развертывание

**Универсальный скрипт (рекомендуется):**
```bash
python3 scripts/deploy_universal.py
```

**Ручное развертывание:**
```bash
# Скопировать скрипт на сервер
scp scripts/deploy_universal.sh root@your-server:/tmp/
ssh root@your-server "chmod +x /tmp/deploy_universal.sh && /tmp/deploy_universal.sh"

# Скопировать файлы проекта
scp -r . root@your-server:/opt/dive-color-corrector/

# Запустить сервис
ssh root@your-server "systemctl start dive-color-corrector.service"
```

### Локальная разработка

```bash
pip install -r src/requirements.txt
python app.py
```

Сервер будет доступен по адресу: http://localhost

## 📚 API Endpoints

### Основные
- `GET /health` - Проверка работоспособности
- `GET /docs` - Документация API

### Мобильный API
- `GET /api/mobile/status` - Статус API
- `GET /api/mobile/health` - Проверка здоровья
- `POST /api/mobile/process/image` - Обработка изображения
- `POST /api/mobile/process/video` - Обработка видео
- `GET /api/mobile/files` - Список файлов
- `GET /api/download/{filename}` - Скачивание файла

### Поддерживаемые форматы

**Изображения:**
- JPG, JPEG, PNG, BMP

**Видео:**
- MP4, AVI, MOV, MKV

**Ограничения:**
- Максимальный размер файла: 500MB

## 🔧 Управление сервисом

### Основные команды
```bash
# Статус сервиса
sudo systemctl status dive-color-corrector.service

# Запуск/остановка/перезапуск
sudo systemctl start dive-color-corrector.service
sudo systemctl stop dive-color-corrector.service
sudo systemctl restart dive-color-corrector.service
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

## 💡 Примеры использования

### Обработка изображения
```bash
curl -X POST "http://your-server/api/mobile/process/image" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-image.jpg"
```

### Обработка видео
```bash
curl -X POST "http://your-server/api/mobile/process/video" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-video.mp4"
```

### Проверка статуса
```bash
curl http://your-server/api/mobile/status
```

## ⚠️ Важные особенности

- **Автоматическая очистка файлов** при загрузке новых
- **Ограничения**: максимальный размер файла 500MB
- **Универсальность**: работает на Debian и Ubuntu
- **Мягкая очистка диска** еженедельно в воскресенье в 3:00

## 📊 Мониторинг

- **Health check:** `curl http://your-server/health`
- **Логи:** `docker-compose logs -f api`
- **Статус API:** `curl http://your-server/api/mobile/status`
- **Мониторинг системы:** `/opt/dive-color-corrector/monitor.sh`
- **Проверка диска:** `/opt/check_disk.sh`

## 📚 Документация

- **API документация:** http://your-server/docs
- **Swagger UI:** http://your-server/docs

## 📝 Лицензия

MIT License

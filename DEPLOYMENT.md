# Развертывание Python API Server с обработкой видео

## Обзор

Оптимизированный API сервер на FastAPI с интеграцией библиотеки dive-color-corrector для обработки видео и изображений. Включает автоматическую очистку файлов и оптимизированные настройки для серверов с ограниченными ресурсами.

## ✨ Особенности

- **Автоматическая очистка файлов** при загрузке новых
- **Оптимизированные настройки** для экономии ресурсов
- **Без авторизации** для упрощения использования
- **Автоматическая очистка диска** каждый день

## Быстрое развертывание на Debian

### 1. Автоматическое развертывание

```bash
# Скачайте и запустите оптимизированный скрипт
wget https://raw.githubusercontent.com/your-repo/pythonServer/main/scripts/deploy_optimized.sh
chmod +x deploy_optimized.sh
sudo ./deploy_optimized.sh
```

### 2. Копирование файлов проекта

```bash
# Скопируйте файлы проекта на сервер
scp -r . root@your-server:/opt/python-api-server/
```

### 3. Запуск сервиса

```bash
# Запустите API сервер
sudo systemctl start python-api-server.service

# Проверьте статус
sudo systemctl status python-api-server.service
```

### 3. Ручное развертывание

Если автоматическое развертывание не работает:

```bash
# 1. Скопируйте скрипт развертывания на сервер
scp scripts/deploy_debian.sh root@your-server:/tmp/

# 2. Подключитесь к серверу
ssh root@your-server

# 3. Запустите скрипт развертывания
chmod +x /tmp/deploy_debian.sh
/tmp/deploy_debian.sh

# 4. Скопируйте файлы проекта
rsync -avz --exclude=.git --exclude=__pycache__ . root@your-server:/opt/python-api-server/

# 5. Запустите сервис
systemctl start python-api-server.service
```

## Конфигурация

### server_config.json

```json
{
  "server": {
    "host": "your-server-ip",
    "port": 22,
    "username": "root",
    "auth_method": "password",
    "password": "your-password",
    "os": "debian"
  },
  "deployment": {
    "app_name": "python-api-server",
    "app_port": 8000,
    "domain": "your-server-ip",
    "ssl_enabled": false,
    "firewall_ports": [22, 80, 443, 8000]
  }
}
```

## API Endpoints

После развертывания API будет доступен по адресу: `http://your-server:8000`

### Основные endpoints:

- `GET /` - Проверка работоспособности
- `GET /health` - Детальная проверка здоровья
- `GET /docs` - Документация API (Swagger UI)

### Обработка файлов:

- `POST /api/process/image` - Обработка изображения
- `POST /api/process/video` - Обработка видео (streaming)
- `GET /api/download/{filename}` - Скачивание обработанного файла
- `GET /api/files` - Список обработанных файлов
- `DELETE /api/files/{filename}` - Удаление файла

### Доступ:

API доступен без авторизации для упрощения использования.

## Управление сервисом

### Systemd команды:

```bash
# Статус сервиса
systemctl status python-api-server.service

# Запуск сервиса
systemctl start python-api-server.service

# Остановка сервиса
systemctl stop python-api-server.service

# Перезапуск сервиса
systemctl restart python-api-server.service

# Включение автозапуска
systemctl enable python-api-server.service
```

### Полезные скрипты:

```bash
# Мониторинг системы
/opt/python-api-server/monitor.sh

# Обновление приложения
/opt/python-api-server/update.sh

# Просмотр логов
docker-compose logs -f
```

## Мониторинг и обслуживание

### Автоматическая очистка

Система автоматически удаляет старые файлы:
- Загруженные файлы старше 7 дней
- Обработанные файлы старше 7 дней  
- Логи старше 30 дней

### Мониторинг ресурсов

```bash
# Проверка использования диска
df -h /opt/python-api-server

# Проверка использования памяти
free -h

# Статус Docker контейнеров
docker-compose ps
```

## Локальная разработка

### Запуск с Docker:

```bash
make deploy-local
```

### Запуск без Docker:

```bash
# Установка зависимостей
make install

# Запуск сервера
make run
```

## Устранение неполадок

### Сервис не запускается:

1. Проверьте логи:
   ```bash
   journalctl -u python-api-server.service -f
   ```

2. Проверьте Docker:
   ```bash
   docker-compose logs
   ```

3. Проверьте конфигурацию:
   ```bash
   cat /opt/python-api-server/.env
   ```

### API недоступен:

1. Проверьте файрвол:
   ```bash
   ufw status
   ```

2. Проверьте порт:
   ```bash
   netstat -tlnp | grep 8000
   ```

3. Проверьте Docker контейнеры:
   ```bash
   docker-compose ps
   ```

### Проблемы с обработкой видео:

1. Проверьте доступное место на диске
2. Убедитесь, что OpenCV установлен корректно
3. Проверьте права доступа к директориям uploads/outputs

## Безопасность

- Файрвол настроен на минимально необходимые порты
- Автоматическая очистка старых файлов
- API доступен без авторизации для упрощения использования
- Автоматическая очистка диска каждый день

## Обновление

Для обновления приложения:

```bash
# Автоматическое обновление
/opt/python-api-server/update.sh

# Или через Makefile
make deploy-debian
```

## Поддержка

При возникновении проблем:

1. Проверьте логи сервиса
2. Убедитесь в корректности конфигурации
3. Проверьте доступность ресурсов сервера
4. Обратитесь к документации API: `http://your-server:8000/docs`

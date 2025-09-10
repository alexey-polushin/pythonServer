# 🎥 Video Processing Server

Сервер для обработки видео с коррекцией цветов для дайвинга.

## 🚀 Быстрый старт

### Развертывание на сервере

1. **Настройте конфигурацию сервера:**
```bash
cp server_config.example.json server_config.json
# Отредактируйте server_config.json с вашими данными
```

2. **Запустите развертывание:**
```bash
./deploy_optimized.sh
```

3. **Для обновления кода:**
```bash
./deploy_update.sh
```

## 📋 Требования

### Основные зависимости (requirements_server.txt):
- Python 3.12+
- FastAPI 0.104.1
- Uvicorn 0.24.0
- OpenCV 4.8.0+
- NumPy 1.24.0+
- Pydantic 2.5.0
- psutil 5.9.0+

### Дополнительные зависимости (src/requirements.txt):
- SQLAlchemy 2.0.23 (база данных)
- Redis 5.0.1 (кеширование)
- Celery 5.3.4 (фоновые задачи)
- CuPy CUDA 12.3.0 (GPU ускорение)
- Gunicorn 21.2.0 (WSGI сервер)

### Системные требования:
- Nginx (устанавливается автоматически)
- Redis (для кеширования и очередей)

## 🔧 API Endpoints

### Основные
- `GET /` - Проверка работоспособности
- `GET /health` - Статус здоровья
- `GET /docs` - Документация API (Swagger UI)

### Обработка файлов
- `POST /api/process/image` - Обработка изображений
- `POST /api/process/video` - Обработка видео
- `GET /api/download/{filename}` - Скачивание файлов
- `GET /api/files` - Список файлов
- `DELETE /api/files/{filename}` - Удаление файлов

### Мобильный API
- `GET /api/mobile/status` - Статус мобильного API
- `GET /api/mobile/health` - Здоровье мобильного API
- `POST /api/mobile/process/image` - Мобильная обработка изображений
- `POST /api/mobile/process/video` - Мобильная обработка видео
- `GET /api/mobile/files` - Мобильные файлы

### Производительность
- `GET /api/performance/info` - Информация о производительности
- `POST /api/performance/configure` - Настройка производительности

## ⚙️ Настройки производительности

Сервер автоматически определяет оптимальные настройки на основе характеристик:

- **Batch size**: размер батча для обработки кадров
- **Max processes**: максимальное количество процессов
- **Video quality**: качество выходного видео (1-100%)
- **GPU**: использование GPU ускорения (CUDA, если доступно)
- **Auto configure**: автоматическая настройка параметров
- **FFmpeg optimization**: оптимизация кодирования видео

### Профили серверов:
- **LOW_END**: 2 CPU, 2GB RAM → batch=16, proc=2, quality=75%
- **STANDARD**: 4 CPU, 8GB RAM → batch=48, proc=3, quality=80%
- **MID_RANGE**: 8 CPU, 16GB RAM → batch=96, proc=6, quality=85%
- **HIGH_END**: 16+ CPU, 32+ GB RAM → batch=128, proc=16, quality=90%

### GPU ускорение:
- **CuPy CUDA 12.3.0**: для обработки на GPU
- **Автоматическое определение**: наличия CUDA
- **Fallback на CPU**: если GPU недоступен

## 🛠️ Управление сервером

### Команды systemd:
```bash
systemctl status video-server    # Статус сервиса
systemctl restart video-server   # Перезапуск
systemctl stop video-server      # Остановка
systemctl start video-server     # Запуск
```

### Мониторинг:
```bash
# На сервере
cd /opt/video-server
source venv/bin/activate
python scripts/performance_monitor.py
```

### Оптимизация:
```bash
# На сервере
python scripts/remote_server_optimizer.py
python scripts/set_quality_profile.py list
```

## 📁 Структура проекта

```
pythonServer/
├── app.py                     # Основное приложение
├── deploy_optimized.sh        # Полное развертывание
├── deploy_update.sh           # Быстрое обновление
├── .deployignore              # Исключения при развертывании
├── requirements_server.txt    # Зависимости для сервера
├── server_config.json         # Конфигурация сервера
├── performance_config.json    # Настройки производительности
├── src/                       # Исходный код
│   ├── api/                   # API endpoints
│   ├── config/                # Конфигурация
│   ├── dive_color_corrector/  # Обработка видео
│   ├── models/                # Модели данных
│   └── services/              # Сервисы
├── scripts/                   # Скрипты сервера
│   ├── auto_setup_server.py
│   ├── performance_monitor.py
│   ├── remote_server_optimizer.py
│   ├── set_quality_profile.py
│   └── ...
├── tests/                     # Тесты
└── uploads/                   # Загруженные файлы
```

## 🌐 Архитектура

```
Интернет → Nginx (порты 80/443) → FastAPI (порт 8080) → Redis (порт 6379)
```

- **Nginx**: reverse proxy, SSL терминация, обработка статических файлов
- **FastAPI**: API сервер, обработка видео
- **Redis**: кеширование, очереди задач, сессии
- **Systemd**: управление сервисами
- **Docker**: контейнеризация (опционально)

## 🔒 Безопасность

- Nginx как reverse proxy с SSL поддержкой
- Файрвол настроен (порты 22, 80, 443)
- Изолированная среда Python (venv)
- Логирование всех операций
- SSL сертификаты в папке `docker/ssl/`

## 📊 Мониторинг

### Логи:
```bash
journalctl -u video-server -f    # Логи приложения
journalctl -u nginx -f          # Логи nginx
```

### Метрики:
- CPU, RAM, диск через `psutil`
- Производительность обработки видео
- Статистика API запросов

## 🚀 Развертывание

### Автоматическое развертывание:
1. Скопируйте `server_config.example.json` в `server_config.json`
2. Настройте параметры сервера
3. Запустите `./deploy_optimized.sh`

### Docker развертывание:
```bash
cd docker/
docker-compose up -d
```

### Что происходит при развертывании:
1. Установка системных зависимостей
2. Копирование кода (с исключениями)
3. Создание Python окружения
4. Установка зависимостей
5. Настройка nginx
6. Создание systemd сервиса
7. Оптимизация настроек производительности
8. Запуск сервисов
9. Настройка Redis для кеширования

## 📝 Поддерживаемые форматы

### Видео:
- MP4, AVI, MOV, MKV, WMV, FLV, WebM

### Изображения:
- JPG, JPEG, PNG, BMP

## 🎯 Особенности

- **Автоматическая оптимизация** под характеристики сервера
- **Многопроцессная обработка** для ускорения
- **GPU ускорение** (если доступно)
- **Коррекция цветов** для подводной съемки
- **REST API** с документацией
- **Мониторинг производительности**
- **Быстрое развертывание**

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `journalctl -u video-server`
2. Проверьте статус: `systemctl status video-server`
3. Проверьте nginx: `systemctl status nginx`
4. Проверьте API: `curl http://your-server/health`
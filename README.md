# Python API Server

Современный Python API сервер на FastAPI для общения с клиентами.

## 📁 Структура проекта

```
pythonServer/
├── src/                          # Исходный код приложения
│   ├── api/                      # API слой
│   │   ├── __init__.py
│   │   ├── main.py              # Основной файл FastAPI приложения
│   │   └── routes.py            # API маршруты
│   ├── config/                   # Конфигурация
│   │   ├── __init__.py
│   │   └── settings.py          # Настройки приложения
│   ├── models/                   # Модели данных
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic схемы
│   └── requirements.txt          # Python зависимости
├── docker/                       # Docker конфигурация
│   ├── Dockerfile               # Docker образ
│   ├── docker-compose.yml       # Docker Compose
│   └── nginx/                   # Nginx конфигурация
│       └── nginx.conf
├── scripts/                      # Скрипты развертывания
│   ├── deploy.sh                # Автоматическое развертывание
│   ├── deploy_with_config.py    # Python скрипт развертывания
│   ├── server_config.json.example
│   ├── deploy.yml               # Ansible playbook
│   └── env.j2                   # Шаблон переменных окружения
├── docs/                         # Документация
│   ├── README.md                # Основная документация
│   └── INSTALL.md               # Инструкции по установке
├── tests/                        # Тесты (будущее расширение)
├── app.py                       # Точка входа приложения
├── .gitignore                   # Git ignore файл
└── README.md                    # Этот файл
```

## 🚀 Возможности

- **RESTful API** с автоматической документацией
- **Аутентификация** через Bearer токены
- **CORS поддержка** для работы с клиентами
- **Логирование** всех операций
- **Docker контейнеризация** для легкого развертывания
- **Nginx reverse proxy** для production
- **Модульная архитектура** с разделением на слои

## 🛠 Быстрый старт

### Локальная разработка

1. **Установите зависимости:**
```bash
pip install -r src/requirements.txt
```

2. **Запустите сервер:**
```bash
python app.py
```

Сервер будет доступен по адресу: http://localhost:8000

### Docker развертывание

1. **Соберите и запустите контейнеры:**
```bash
cd docker
docker-compose up -d --build
```

2. **Сервер будет доступен по адресу:** http://localhost

## 📚 API Endpoints

### Основные

- `GET /` - Проверка работоспособности
- `GET /health` - Детальная проверка здоровья
- `GET /docs` - Автоматическая документация API

### API (требует аутентификации)

- `POST /api/message` - Отправка сообщения
- `GET /api/messages` - Получение последних сообщений
- `GET /api/messages/{id}` - Получение конкретного сообщения
- `DELETE /api/messages/{id}` - Удаление сообщения
- `GET /api/stats` - Статистика сервера

## 🔐 Аутентификация

Все API endpoints требуют Bearer токен в заголовке:
```
Authorization: Bearer your-secret-token
```

## 🏗 Архитектура

### Слои приложения:

1. **API Layer** (`src/api/`) - FastAPI роуты и обработчики
2. **Models Layer** (`src/models/`) - Pydantic схемы данных
3. **Config Layer** (`src/config/`) - Настройки и конфигурация
4. **Docker Layer** (`docker/`) - Контейнеризация и развертывание

### Принципы:

- **Разделение ответственности** - каждый модуль отвечает за свою область
- **Модульность** - легко добавлять новые функции
- **Конфигурируемость** - все настройки вынесены в конфиг
- **Масштабируемость** - готовность к росту нагрузки

## 🚀 Развертывание на VDS

Подробные инструкции смотрите в [docs/INSTALL.md](docs/INSTALL.md)

### Краткая инструкция:

1. **Подготовьте конфигурацию:**
```bash
cp scripts/server_config.json.example scripts/server_config.json
# Отредактируйте server_config.json с вашими данными
```

2. **Запустите развертывание:**
```bash
python scripts/deploy_with_config.py
```

## 🔧 Управление

### Локальная разработка:
```bash
# Запуск в режиме разработки
python app.py

# Запуск с Docker
cd docker && docker-compose up -d
```

### Production:
```bash
# Подключение к серверу
ssh root@your-server-ip

# Управление сервисами
cd /opt/python-api-server
docker-compose logs -f api      # Просмотр логов
docker-compose restart          # Перезапуск
docker-compose down             # Остановка
```

## 📊 Мониторинг

- **Health check:** `curl http://your-domain/health`
- **Логи:** `docker-compose logs -f api`
- **Статистика:** `curl -H "Authorization: Bearer token" http://your-domain/api/stats`

## 🔒 Безопасность

1. Измените секретные ключи в .env файле
2. Настройте firewall (откройте только порты 80, 443, 22)
3. Используйте HTTPS в продакшене
4. Регулярно обновляйте зависимости

## 🚀 Масштабирование

Для увеличения производительности:

1. Увеличьте количество worker процессов в Dockerfile
2. Добавьте load balancer
3. Используйте внешнюю базу данных
4. Настройте Redis кластер

## 📝 Лицензия

MIT License

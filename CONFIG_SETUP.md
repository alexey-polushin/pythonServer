# Настройка конфигурации сервера

## Быстрый старт

1. **Скопируйте пример конфига:**
   ```bash
   cp server_config.example.json server_config.json
   ```

2. **Отредактируйте конфиг:**
   ```bash
   nano server_config.json
   ```

3. **Заполните данные вашего сервера:**
   - `host` - IP адрес сервера
   - `username` - имя пользователя (обычно `root`)
   - `password` - пароль для SSH
   - `domain` - домен или IP для доступа к API

## Пример конфигурации

```json
{
  "server": {
    "host": "95.81.76.7",
    "username": "root",
    "password": "your-secure-password"
  },
  "deployment": {
    "app_name": "python-api-server",
    "app_port": 8000,
    "domain": "95.81.76.7"
  }
}
```

## Безопасность

- ✅ `server_config.json` добавлен в `.gitignore`
- ✅ Пароли и секретные данные не попадают в git
- ✅ Используйте `server_config.example.json` как шаблон

## Развертывание

После настройки конфига:

```bash
# Развертывание на сервере
make deploy-debian

# Или напрямую
python scripts/deploy_with_config.py server_config.json
```

## Мониторинг

```bash
# Проверка состояния сервера
make server-monitor

# Очистка диска на сервере
make server-cleanup
```

## Поддерживаемые ОС

- ✅ Debian/Ubuntu
- ✅ CentOS/RHEL (с небольшими изменениями)
- ✅ Docker контейнеры

## Проблемы

Если возникают проблемы:

1. Проверьте SSH соединение:
   ```bash
   ssh root@your-server-ip
   ```

2. Убедитесь, что порты открыты:
   - 22 (SSH)
   - 8000 (API)

3. Проверьте логи:
   ```bash
   make deploy-logs
   ```

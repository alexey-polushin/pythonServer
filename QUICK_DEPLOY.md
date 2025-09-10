# Быстрое развертывание сервера

## Настройка конфигурации

Перед развертыванием создайте файл `server_config.json` на основе примера:

```bash
# Скопировать пример конфигурации
cp server_config.example.json server_config.json

# Отредактировать конфигурацию
nano server_config.json
```

Укажите в конфигурации:
- `host`: IP адрес вашего сервера
- `password`: пароль для доступа к серверу
- `domain`: домен или IP сервера

## Автоматическое развертывание (рекомендуется)

```bash
# 1. Диагностика проблем
make deploy-troubleshoot

# 2. Развертывание улучшенным скриптом
make deploy-debian
```

## Ручное развертывание (если автоматическое не работает)

### Подготовка
```bash
# Очистить SSH ключи
ssh-keygen -R ВАШ_IP_СЕРВЕРА

# Установить sshpass (если не установлен)
brew install hudochenkov/sshpass/sshpass
```

### Развертывание
```bash
# 1. Выполнить скрипт развертывания на сервере
sshpass -p "ВАШ_ПАРОЛЬ" scp -o StrictHostKeyChecking=no scripts/deploy_optimized.sh root@ВАШ_IP:/tmp/
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "chmod +x /tmp/deploy_optimized.sh && /tmp/deploy_optimized.sh"

# 2. Скопировать файлы проекта
sshpass -p "ВАШ_ПАРОЛЬ" rsync -avz --progress --exclude=.git --exclude=__pycache__ --exclude='*.pyc' --exclude=.env --exclude=uploads/ --exclude=outputs/ --exclude=logs/ ./ root@ВАШ_IP:/opt/python-api-server/

# 3. Подготовить Docker файлы
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "cd /opt/python-api-server && cp docker/docker-compose.yml . && cp docker/Dockerfile ."

# 4. Запустить контейнеры
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "cd /opt/python-api-server && docker-compose down && docker-compose up -d api redis"

# 5. Проверить статус
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "cd /opt/python-api-server && docker-compose ps && curl -f http://localhost:8000/health"
```

## Проверка развертывания

```bash
# Проверить API
curl http://ВАШ_IP:8000/health

# Проверить мобильный API
curl http://ВАШ_IP:8000/api/mobile/status

# Открыть документацию
open http://ВАШ_IP:8000/docs
```

## Полезные команды

```bash
# Статус на сервере
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "/opt/python-api-server/monitor.sh"

# Логи контейнеров
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "cd /opt/python-api-server && docker-compose logs api --tail=50"

# Перезапуск сервиса
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "cd /opt/python-api-server && docker-compose restart api"
```

## Адреса после развертывания

- **API**: http://ВАШ_IP:8000
- **Документация**: http://ВАШ_IP:8000/docs
- **Мобильный API**: http://ВАШ_IP:8000/api/mobile/status
- **Health Check**: http://ВАШ_IP:8000/health

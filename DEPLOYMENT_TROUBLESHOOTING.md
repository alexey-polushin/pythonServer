# Руководство по развертыванию и устранению проблем

## Настройка конфигурации

Перед развертыванием создайте файл `server_config.json`:

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

## Известные проблемы и их решения

### 1. Проблема с SSH ключами хоста

**Проблема**: При переустановке сервера возникает ошибка:
```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
```

**Решение**:
```bash
# Очистить старый SSH ключ
ssh-keygen -R <IP_СЕРВЕРА>

# Или использовать улучшенный скрипт
python scripts/deploy_improved.py
```

### 2. Проблема с путями Docker файлов

**Проблема**: `docker-compose` не может найти `docker-compose.yml` и `Dockerfile`

**Решение**:
```bash
# На сервере скопировать файлы в корень проекта
cd /opt/python-api-server
cp docker/docker-compose.yml .
cp docker/Dockerfile .
```

### 3. Проблема с systemd сервисом

**Проблема**: Сервис конфликтует с ручным запуском контейнеров

**Решение**:
```bash
# Остановить сервис перед ручным запуском
systemctl stop python-api-server.service

# Запустить контейнеры
docker-compose up -d api redis

# Запустить сервис
systemctl start python-api-server.service
```

### 4. Проблема с доступом к Docker Hub

**Проблема**: Ошибка 403 Forbidden при пересборке образов

**Решение**:
```bash
# Использовать существующие образы вместо пересборки
docker-compose up -d api redis

# Не использовать --build если не нужно
```

### 5. Проблема с sshpass на macOS

**Проблема**: `sshpass: Failed to run command: No such file or directory`

**Решение**:
```bash
# Установить sshpass через Homebrew
brew install hudochenkov/sshpass/sshpass

# Проверить путь
which sshpass
```

## Улучшенный процесс развертывания

### Использование улучшенного скрипта

```bash
# Использовать новый скрипт вместо старого
python scripts/deploy_improved.py server_config.json
```

### Ручное развертывание (если скрипт не работает)

1. **Очистить SSH ключи**:
```bash
ssh-keygen -R ВАШ_IP_СЕРВЕРА
```

2. **Проверить соединение**:
```bash
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "echo 'Connection successful'"
```

3. **Скопировать скрипт развертывания**:
```bash
sshpass -p "ВАШ_ПАРОЛЬ" scp -o StrictHostKeyChecking=no scripts/deploy_optimized.sh root@ВАШ_IP:/tmp/
```

4. **Выполнить развертывание**:
```bash
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "chmod +x /tmp/deploy_optimized.sh && /tmp/deploy_optimized.sh"
```

5. **Скопировать файлы проекта**:
```bash
sshpass -p "ВАШ_ПАРОЛЬ" rsync -avz --progress --exclude=.git --exclude=__pycache__ --exclude='*.pyc' --exclude=.env --exclude=uploads/ --exclude=outputs/ --exclude=logs/ ./ root@ВАШ_IP:/opt/python-api-server/
```

6. **Подготовить Docker файлы**:
```bash
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "cd /opt/python-api-server && cp docker/docker-compose.yml . && cp docker/Dockerfile ."
```

7. **Запустить контейнеры**:
```bash
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "cd /opt/python-api-server && docker-compose down && docker-compose up -d api redis"
```

8. **Проверить статус**:
```bash
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "cd /opt/python-api-server && docker-compose ps && curl -f http://localhost:8000/health"
```

## Диагностика проблем

### Проверка статуса контейнеров
```bash
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "cd /opt/python-api-server && docker-compose ps"
```

### Просмотр логов
```bash
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "cd /opt/python-api-server && docker-compose logs api --tail=50"
```

### Проверка доступности API
```bash
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "curl -f http://localhost:8000/health"
```

### Проверка systemd сервиса
```bash
sshpass -p "ВАШ_ПАРОЛЬ" ssh -o StrictHostKeyChecking=no root@ВАШ_IP "systemctl status python-api-server.service --no-pager"
```

## Рекомендации

1. **Всегда используйте улучшенный скрипт** `deploy_improved.py`
2. **Проверяйте SSH ключи** перед развертыванием
3. **Не пересобирайте образы** без необходимости
4. **Координируйте** systemd сервис и ручной запуск
5. **Используйте мониторинг** для отслеживания состояния

## Полезные команды

```bash
# Мониторинг на сервере
/opt/python-api-server/monitor.sh

# Очистка диска
/opt/disk_cleanup.sh

# Проверка диска
/opt/check_disk.sh

# Обновление сервиса
/opt/python-api-server/update.sh
```

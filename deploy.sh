#!/bin/bash

# Быстрый деплой скрипт
set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Python API Server - Быстрый деплой${NC}"
echo "=================================="

# Проверяем наличие конфигурации
if [ ! -f "server_config.json" ]; then
    echo -e "${RED}❌ Файл server_config.json не найден${NC}"
    echo -e "${YELLOW}💡 Создайте его на основе server_config.example.json${NC}"
    exit 1
fi

# Проверяем аргументы
if [ "$1" = "update" ]; then
    echo -e "${YELLOW}🔄 Режим: Обновление кода${NC}"
    python3 scripts/deploy_update.py
elif [ "$1" = "deploy" ] || [ -z "$1" ]; then
    echo -e "${YELLOW}🚀 Режим: Полное развертывание${NC}"
    python3 scripts/deploy_universal.py
else
    echo -e "${RED}❌ Неизвестный режим: $1${NC}"
    echo -e "${YELLOW}Использование:${NC}"
    echo "  ./deploy.sh          - Полное развертывание"
    echo "  ./deploy.sh deploy   - Полное развертывание"
    echo "  ./deploy.sh update   - Обновление кода"
    exit 1
fi

echo -e "${GREEN}✅ Деплой завершен!${NC}"

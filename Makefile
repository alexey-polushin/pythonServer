# Makefile для Python API Server

.PHONY: help deploy update test clean

# Цвета для вывода
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)Python API Server - Команды управления$(NC)"
	@echo "=================================="
	@echo ""
	@echo "$(YELLOW)Развертывание:$(NC)"
	@echo "  make deploy     - Полное развертывание на сервере"
	@echo "  make update     - Обновление кода на сервере"
	@echo ""
	@echo "$(YELLOW)Локальная разработка:$(NC)"
	@echo "  make dev        - Запуск локально для разработки"
	@echo "  make test       - Запуск тестов API"
	@echo "  make clean      - Очистка временных файлов"
	@echo ""
	@echo "$(YELLOW)Утилиты:$(NC)"
	@echo "  make help       - Показать эту справку"
	@echo "  make status     - Проверить статус на сервере"
	@echo ""

deploy: ## Полное развертывание на сервере
	@echo "$(GREEN)🚀 Начинаем полное развертывание...$(NC)"
	python3 scripts/deploy_universal.py

update: ## Обновление кода на сервере
	@echo "$(GREEN)🔄 Обновляем код на сервере...$(NC)"
	python3 scripts/deploy_update.py

dev: ## Запуск локально для разработки
	@echo "$(GREEN)🔧 Запускаем локально для разработки...$(NC)"
	python3 app.py

test: ## Запуск тестов API
	@echo "$(GREEN)🧪 Запускаем тесты API...$(NC)"
	python3 tests/test_api.py

status: ## Проверить статус на сервере
	@echo "$(GREEN)📊 Проверяем статус на сервере...$(NC)"
	@if [ -f server_config.json ]; then \
		HOST=$$(python3 -c "import json; print(json.load(open('server_config.json'))['server']['host'])") && \
		echo "🌐 Проверяем API на http://$$HOST/health" && \
		curl -s http://$$HOST/health | python3 -m json.tool || echo "$(RED)❌ API недоступен$(NC)"; \
	else \
		echo "$(RED)❌ Файл server_config.json не найден$(NC)"; \
	fi

clean: ## Очистка временных файлов
	@echo "$(GREEN)🧹 Очищаем временные файлы...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	@echo "$(GREEN)✅ Очистка завершена$(NC)"

# Проверка зависимостей
check-deps:
	@echo "$(GREEN)🔍 Проверяем зависимости...$(NC)"
	@python3 -c "import json, subprocess, sys; print('✅ Python OK')" || (echo "$(RED)❌ Python не найден$(NC)" && exit 1)
	@which ssh > /dev/null && echo "✅ SSH OK" || (echo "$(RED)❌ SSH не найден$(NC)" && exit 1)
	@which rsync > /dev/null && echo "✅ rsync OK" || (echo "$(RED)❌ rsync не найден$(NC)" && exit 1)
	@echo "$(GREEN)✅ Все зависимости установлены$(NC)"

.PHONY: help install dev test lint format clean docker-build docker-up docker-down

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	pip install -r src/requirements.txt

dev: ## Установить зависимости для разработки
	pip install -r src/requirements.txt
	pip install -r requirements-dev.txt

test: ## Запустить тесты
	pytest tests/ -v

lint: ## Проверить код линтером
	flake8 src/ tests/
	mypy src/

format: ## Форматировать код
	black src/ tests/

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/

docker-build: ## Собрать Docker образ
	cd docker && docker-compose build

docker-up: ## Запустить Docker контейнеры
	cd docker && docker-compose up -d

docker-down: ## Остановить Docker контейнеры
	cd docker && docker-compose down

docker-logs: ## Показать логи Docker контейнеров
	cd docker && docker-compose logs -f

run: ## Запустить приложение локально
	python app.py

deploy: ## Развернуть на сервере (улучшенная версия)
	python scripts/deploy_improved.py

deploy-debian: ## Развернуть на Debian сервере (улучшенная версия)
	python scripts/deploy_improved.py server_config.json

deploy-legacy: ## Развернуть на сервере (старая версия)
	python scripts/deploy_with_config.py

deploy-local: ## Развернуть локально с Docker
	cd docker && docker-compose up -d --build

deploy-status: ## Проверить статус развертывания
	@echo "🔍 Проверяем статус сервисов..."
	@if command -v docker-compose >/dev/null 2>&1; then \
		cd docker && docker-compose ps; \
	else \
		echo "Docker Compose не установлен"; \
	fi

deploy-logs: ## Показать логи развертывания
	@echo "📋 Показываем логи..."
	@if command -v docker-compose >/dev/null 2>&1; then \
		cd docker && docker-compose logs -f; \
	else \
		echo "Docker Compose не установлен"; \
	fi

test-mobile: ## Тестировать мобильный API
	python test_mobile_api.py

test-api: ## Тестировать основной API
	python test_api.py

mobile-docs: ## Показать документацию мобильного API
	@echo "📱 Документация мобильного API:"
	@echo "  - Статус: GET /api/mobile/status"
	@echo "  - Здоровье: GET /api/mobile/health"
	@echo "  - Обработка изображений: POST /api/mobile/process/image"
	@echo "  - Список файлов: GET /api/mobile/files"
	@echo "  - Обработка видео: POST /api/process/video (streaming)"
	@echo "  - Скачивание: GET /api/download/{filename}"

server-cleanup: ## Запустить очистку диска на сервере
	sshpass -p jN1lW2vX6dkQ ssh root@95.81.76.7 "/opt/disk_cleanup.sh"

server-monitor: ## Проверить состояние сервера
	sshpass -p jN1lW2vX6dkQ ssh root@95.81.76.7 "/opt/check_disk.sh"

local-cleanup: ## Запустить локальную очистку (macOS)
	@echo "🧹 Локальная очистка macOS..."
	@echo "📊 Состояние диска:"
	@df -h /
	@echo ""
	@echo "🗑️ Очищаем временные файлы..."
	@rm -rf ~/Library/Caches/*
	@rm -rf /tmp/*
	@echo "✅ Локальная очистка завершена!"

local-monitor: ## Проверить состояние локальной системы
	@echo "📊 Мониторинг локальной системы:"
	@echo "Дата: $$(date)"
	@echo ""
	@echo "💾 Использование диска:"
	@df -h /
	@echo ""
	@echo "🧠 Использование памяти:"
	@vm_stat | head -10
	@echo ""
	@echo "📈 Нагрузка:"
	@uptime

deploy-troubleshoot: ## Диагностика проблем развертывания
	@echo "🔍 Диагностика проблем развертывания..."
	@echo "1. Проверяем SSH ключи..."
	@echo "   Запустите: ssh-keygen -R ВАШ_IP_СЕРВЕРА"
	@echo "2. Проверяем sshpass..."
	@which sshpass || echo "sshpass не установлен. Установите: brew install hudochenkov/sshpass/sshpass"
	@echo "3. Проверяем конфигурацию..."
	@if [ -f server_config.json ]; then echo "✅ server_config.json найден"; else echo "❌ server_config.json не найден"; fi
	@echo "4. Проверяем Docker файлы..."
	@if [ -f docker/docker-compose.yml ]; then echo "✅ docker-compose.yml найден"; else echo "❌ docker-compose.yml не найден"; fi
	@if [ -f docker/Dockerfile ]; then echo "✅ Dockerfile найден"; else echo "❌ Dockerfile не найден"; fi
	@echo "5. Проверяем улучшенный скрипт..."
	@if [ -f scripts/deploy_improved.py ]; then echo "✅ deploy_improved.py найден"; else echo "❌ deploy_improved.py не найден"; fi

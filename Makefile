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

deploy: ## Развернуть на сервере
	python scripts/deploy_with_config.py

deploy-debian: ## Развернуть на Debian сервере
	python scripts/deploy_with_config.py server_config.json

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

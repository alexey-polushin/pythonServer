# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости для OpenCV headless и обработки видео
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libglib2.0-0 \
    libgomp1 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY src/requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY src/ ./src/
COPY app.py .

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app

# Создаем директории для загрузок и выходных файлов
RUN mkdir -p /app/uploads /app/outputs

# Устанавливаем права доступа
RUN chown -R app:app /app

# Переключаемся на пользователя app
USER app

# Открываем порт
EXPOSE 8080

# Команда запуска (теперь безопасно от пользователя app)
CMD ["gunicorn", "app:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--timeout", "60", "--max-requests", "1000", "--preload"]

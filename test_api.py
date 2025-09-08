#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API endpoints
"""

import requests
import json
import os
from pathlib import Path

# Конфигурация
API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Тестирует health check endpoint"""
    print("🔍 Тестируем health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check прошел успешно")
            print(f"📊 Ответ: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка health check: {e}")
        return False

def test_image_processing():
    """Тестирует обработку изображения"""
    print("\n🖼️ Тестируем обработку изображения...")
    
    # Создаем тестовое изображение
    test_image_path = "test_image.jpg"
    if not os.path.exists(test_image_path):
        print("❌ Тестовое изображение не найдено")
        return False
    
    try:
        with open(test_image_path, "rb") as f:
            files = {"file": ("test_image.jpg", f, "image/jpeg")}
            response = requests.post(
                f"{API_BASE_URL}/api/process/image",
                files=files
            )
        
        if response.status_code == 200:
            print("✅ Обработка изображения прошла успешно")
            result = response.json()
            print(f"📊 Результат: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Ошибка обработки изображения: {response.status_code}")
            print(f"📋 Ответ: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при обработке изображения: {e}")
        return False

def test_file_listing():
    """Тестирует получение списка файлов"""
    print("\n📁 Тестируем получение списка файлов...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/files")
        
        if response.status_code == 200:
            print("✅ Получение списка файлов прошло успешно")
            files = response.json().get("files", [])
            print(f"📊 Найдено файлов: {len(files)}")
            for file_info in files[:3]:  # Показываем первые 3 файла
                print(f"  - {file_info['filename']} ({file_info['size']} bytes)")
            return True
        else:
            print(f"❌ Ошибка получения списка файлов: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при получении списка файлов: {e}")
        return False

def test_api_docs():
    """Тестирует доступность документации API"""
    print("\n📚 Тестируем документацию API...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ Документация API доступна")
            print(f"🌐 URL: {API_BASE_URL}/docs")
            return True
        else:
            print(f"❌ Документация API недоступна: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке документации: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование Python API Server")
    print("=" * 50)
    
    # Проверяем доступность API
    if not test_health_check():
        print("\n❌ API недоступен. Убедитесь, что сервер запущен.")
        return
    
    # Тестируем документацию
    test_api_docs()
    
    # Тестируем получение списка файлов
    test_file_listing()
    
    # Тестируем обработку изображения (если есть тестовое изображение)
    if os.path.exists("test_image.jpg"):
        test_image_processing()
    else:
        print("\n⚠️ Тестовое изображение не найдено. Создайте test_image.jpg для тестирования обработки.")
    
    print("\n🎉 Тестирование завершено!")
    print(f"📚 Документация API: {API_BASE_URL}/docs")

if __name__ == "__main__":
    main()

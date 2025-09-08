#!/usr/bin/env python3
"""
Тестовый скрипт для проверки мобильного API
"""

import requests
import json
import os
from pathlib import Path

# Конфигурация
API_BASE_URL = "http://95.81.76.7:8000"

def test_mobile_status():
    """Тестирует мобильный статус endpoint"""
    print("📱 Тестируем мобильный статус...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/mobile/status")
        if response.status_code == 200:
            print("✅ Мобильный статус получен")
            data = response.json()
            print(f"📊 Статус: {data['status']}")
            print(f"📊 Версия: {data['version']}")
            print(f"📊 Функции: {data['features']}")
            return True
        else:
            print(f"❌ Ошибка получения статуса: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_mobile_health():
    """Тестирует мобильный health check"""
    print("\n🏥 Тестируем мобильный health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/mobile/health")
        if response.status_code == 200:
            print("✅ Мобильный health check прошел")
            data = response.json()
            print(f"📊 Статус: {data['status']}")
            return True
        else:
            print(f"❌ Ошибка health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_mobile_image_processing():
    """Тестирует мобильную обработку изображения"""
    print("\n🖼️ Тестируем мобильную обработку изображения...")
    
    # Создаем тестовое изображение
    test_image_path = "test_image.jpg"
    if not os.path.exists(test_image_path):
        print("❌ Тестовое изображение не найдено")
        return False
    
    try:
        with open(test_image_path, "rb") as f:
            files = {"file": ("test_image.jpg", f, "image/jpeg")}
            response = requests.post(
                f"{API_BASE_URL}/api/mobile/process/image",
                files=files
            )
        
        if response.status_code == 200:
            print("✅ Мобильная обработка изображения прошла успешно")
            result = response.json()
            if result.get("success"):
                data = result["data"]
                print(f"📊 Статус: {data.get('status', 'unknown')}")
                print(f"📊 Выходной файл: {data.get('output_filename', 'unknown')}")
                print(f"📊 Размер файла: {data.get('file_size', 0)} bytes")
            else:
                print(f"❌ Ошибка обработки: {result.get('error', 'unknown')}")
            return True
        else:
            print(f"❌ Ошибка обработки изображения: {response.status_code}")
            print(f"📋 Ответ: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при обработке изображения: {e}")
        return False

def test_mobile_file_listing():
    """Тестирует мобильное получение списка файлов"""
    print("\n📁 Тестируем мобильное получение списка файлов...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/mobile/files")
        
        if response.status_code == 200:
            print("✅ Мобильное получение списка файлов прошло успешно")
            result = response.json()
            if result.get("success"):
                data = result["data"]
                files = data.get("files", [])
                print(f"📊 Найдено файлов: {data.get('count', 0)}")
                for file_info in files[:3]:  # Показываем первые 3 файла
                    print(f"  - {file_info['filename']} ({file_info['size']} bytes)")
            else:
                print(f"❌ Ошибка получения списка: {result.get('error', 'unknown')}")
            return True
        else:
            print(f"❌ Ошибка получения списка файлов: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при получении списка файлов: {e}")
        return False

def test_video_streaming():
    """Тестирует streaming обработку видео"""
    print("\n🎥 Тестируем streaming обработку видео...")
    
    # Создаем тестовое видео
    test_video_path = "test_video.mp4"
    if not os.path.exists(test_video_path):
        print("❌ Тестовое видео не найдено")
        return False
    
    try:
        with open(test_video_path, "rb") as f:
            files = {"file": ("test_video.mp4", f, "video/mp4")}
            response = requests.post(
                f"{API_BASE_URL}/api/process/video",
                files=files,
                stream=True
            )
        
        if response.status_code == 200:
            print("✅ Streaming обработка видео началась")
            print("📊 Получаем прогресс...")
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # Убираем 'data: '
                            if data.get("status") == "analyzing":
                                print(f"📊 Анализ: {data.get('frames_processed', 0)} кадров")
                            elif data.get("status") == "processing":
                                print(f"📊 Обработка: {data.get('progress', 0):.1f}%")
                            elif data.get("status") == "success":
                                print("✅ Обработка видео завершена")
                                print(f"📊 Выходной файл: {data.get('output_filename', 'unknown')}")
                                break
                        except json.JSONDecodeError:
                            continue
            return True
        else:
            print(f"❌ Ошибка обработки видео: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при обработке видео: {e}")
        return False

def main():
    """Главная функция тестирования мобильного API"""
    print("📱 Тестирование мобильного API")
    print("=" * 50)
    
    # Тестируем мобильные endpoints
    test_mobile_status()
    test_mobile_health()
    test_mobile_file_listing()
    
    # Тестируем обработку изображения (если есть тестовое изображение)
    if os.path.exists("test_image.jpg"):
        test_mobile_image_processing()
    else:
        print("\n⚠️ Тестовое изображение не найдено. Создайте test_image.jpg для тестирования.")
    
    # Тестируем обработку видео (если есть тестовое видео)
    if os.path.exists("test_video.mp4"):
        test_video_streaming()
    else:
        print("\n⚠️ Тестовое видео не найдено. Создайте test_video.mp4 для тестирования.")
    
    print("\n🎉 Тестирование мобильного API завершено!")
    print(f"📚 Документация API: {API_BASE_URL}/docs")

if __name__ == "__main__":
    main()

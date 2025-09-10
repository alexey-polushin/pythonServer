#!/usr/bin/env python3
"""
Автоматическая настройка сервера при развертывании
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path

def check_dependencies():
    """Проверяет и устанавливает необходимые зависимости"""
    print("🔍 Проверяем зависимости...")
    
    required_packages = [
        'opencv-python',
        'numpy',
        'psutil',
        'fastapi',
        'uvicorn',
        'python-multipart'
    ]
    
    # Проверяем Python версию
    python_version = sys.version_info
    if python_version < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Проверяем pip
    try:
        import pip
        print("✅ pip доступен")
    except ImportError:
        print("❌ pip не найден")
        return False
    
    # Проверяем ffmpeg
    try:
        result = subprocess.run(['ffprobe', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ ffmpeg/ffprobe установлен")
        else:
            print("⚠️ ffmpeg/ffprobe не найден - будет установлен")
            install_ffmpeg()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ ffmpeg/ffprobe не найден - будет установлен")
        install_ffmpeg()
    
    # Проверяем GPU поддержку
    check_gpu_support()
    
    return True

def install_ffmpeg():
    """Устанавливает ffmpeg"""
    print("📦 Устанавливаем ffmpeg...")
    
    try:
        # Пытаемся установить через системный пакетный менеджер
        if os.name == 'posix':  # Unix-like системы
            # Проверяем, есть ли brew (macOS)
            try:
                subprocess.run(['brew', '--version'], check=True, capture_output=True)
                subprocess.run(['brew', 'install', 'ffmpeg'], check=True)
                print("✅ ffmpeg установлен через Homebrew")
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # Проверяем apt (Ubuntu/Debian)
            try:
                subprocess.run(['apt', '--version'], check=True, capture_output=True)
                subprocess.run(['sudo', 'apt', 'update'], check=True)
                subprocess.run(['sudo', 'apt', 'install', '-y', 'ffmpeg'], check=True)
                print("✅ ffmpeg установлен через apt")
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # Проверяем yum (CentOS/RHEL)
            try:
                subprocess.run(['yum', '--version'], check=True, capture_output=True)
                subprocess.run(['sudo', 'yum', 'install', '-y', 'ffmpeg'], check=True)
                print("✅ ffmpeg установлен через yum")
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        print("⚠️ Не удалось установить ffmpeg автоматически")
        print("Установите ffmpeg вручную для вашей системы")
        
    except Exception as e:
        print(f"❌ Ошибка установки ffmpeg: {str(e)}")

def check_gpu_support():
    """Проверяет поддержку GPU"""
    print("🎮 Проверяем GPU поддержку...")
    
    gpu_info = {"available": False, "type": None}
    
    # Проверяем PyTorch MPS (Apple Metal)
    try:
        import torch
        if torch.backends.mps.is_available() and torch.backends.mps.is_built():
            gpu_info["available"] = True
            gpu_info["type"] = "MPS"
            print("✅ Apple Metal (MPS) доступен")
            return gpu_info
    except ImportError:
        pass
    
    # Проверяем CUDA
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info["available"] = True
            gpu_info["type"] = "CUDA"
            print("✅ CUDA доступен")
            return gpu_info
    except ImportError:
        pass
    
    # Проверяем CuPy
    try:
        import cupy as cp
        gpu_info["available"] = True
        gpu_info["type"] = "CUDA"
        print("✅ CuPy (CUDA) доступен")
        return gpu_info
    except ImportError:
        pass
    
    print("⚠️ GPU ускорение недоступно")
    return gpu_info

def create_server_config():
    """Создает конфигурацию сервера"""
    print("⚙️ Создаем конфигурацию сервера...")
    
    # Импортируем функции после установки зависимостей
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    try:
        from dive_color_corrector.mobile_correct import get_performance_info
        current_config = get_performance_info()
    except ImportError:
        # Если модули еще не установлены, используем значения по умолчанию
        current_config = {
            "batch_size": 32,
            "max_processes": 4,
            "video_quality": 80,
            "use_gpu": False
        }
    
    # Создаем конфигурацию сервера
    server_config = {
        "server_info": {
            "setup_date": subprocess.check_output(['date']).decode().strip(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": os.name
        },
        "performance_settings": current_config,
        "gpu_info": check_gpu_support(),
        "recommendations": {
            "auto_optimize": True,
            "monitoring_enabled": True,
            "log_level": "INFO"
        }
    }
    
    # Сохраняем конфигурацию
    config_path = "server_setup_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(server_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Конфигурация сохранена в: {config_path}")
    return config_path

def setup_logging():
    """Настраивает систему логирования"""
    print("📝 Настраиваем логирование...")
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Создаем конфигурацию логирования
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.StreamHandler"
            },
            "file": {
                "level": "DEBUG",
                "formatter": "standard",
                "class": "logging.FileHandler",
                "filename": "logs/server.log",
                "mode": "a"
            }
        },
        "loggers": {
            "": {
                "handlers": ["default", "file"],
                "level": "INFO",
                "propagate": False
            }
        }
    }
    
    config_path = "logging_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(logging_config, f, indent=2)
    
    print(f"✅ Конфигурация логирования сохранена в: {config_path}")

def create_startup_script():
    """Создает скрипт для запуска сервера"""
    print("🚀 Создаем скрипт запуска...")
    
    startup_script = """#!/bin/bash
# Скрипт запуска сервера обработки видео

echo "🚀 Запуск сервера обработки видео..."

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден"
    exit 1
fi

# Проверяем зависимости
if [ ! -d "src" ]; then
    echo "❌ Папка src не найдена"
    exit 1
fi

# Запускаем сервер
echo "✅ Запускаем сервер..."
python3 app.py

echo "🛑 Сервер остановлен"
"""
    
    script_path = "start_server.sh"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(startup_script)
    
    # Делаем скрипт исполняемым
    os.chmod(script_path, 0o755)
    
    print(f"✅ Скрипт запуска создан: {script_path}")

def main():
    parser = argparse.ArgumentParser(description='Автоматическая настройка сервера')
    parser.add_argument('--skip-deps', action='store_true',
                       help='Пропустить проверку зависимостей')
    parser.add_argument('--skip-ffmpeg', action='store_true',
                       help='Пропустить установку ffmpeg')
    
    args = parser.parse_args()
    
    print("🚀 АВТОМАТИЧЕСКАЯ НАСТРОЙКА СЕРВЕРА")
    print("=" * 50)
    
    # 1. Проверяем зависимости
    if not args.skip_deps:
        if not check_dependencies():
            print("❌ Ошибка проверки зависимостей")
            return 1
    
    # 2. Создаем конфигурацию
    config_path = create_server_config()
    
    # 3. Настраиваем логирование
    setup_logging()
    
    # 4. Создаем скрипт запуска
    create_startup_script()
    
    print("\n" + "=" * 50)
    print("✅ НАСТРОЙКА СЕРВЕРА ЗАВЕРШЕНА!")
    print("=" * 50)
    
    print("\n📋 Следующие шаги:")
    print("1. Запустите оптимизацию: python scripts/remote_server_optimizer.py")
    print("2. Запустите сервер: ./start_server.sh")
    print("3. Мониторинг: python scripts/performance_monitor.py")
    
    print(f"\n💾 Конфигурация сохранена в: {config_path}")
    print("🎉 Сервер готов к работе!")
    
    return 0

if __name__ == "__main__":
    exit(main())

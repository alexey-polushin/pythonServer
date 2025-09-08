#!/usr/bin/env python3
"""
Скрипт для развертывания Python API Server с поддержкой обработки видео
на Debian сервер с использованием конфигурационного файла
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str = "server_config.json") -> Dict[str, Any]:
    """Загружает конфигурацию из JSON файла"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Конфигурационный файл {config_path} не найден")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в конфигурационном файле: {e}")
        sys.exit(1)

def run_ssh_command(host: str, username: str, password: str, command: str) -> bool:
    """Выполняет команду по SSH"""
    try:
        # Используем sshpass для передачи пароля
        cmd = [
            "sshpass", "-p", password,
            f"{username}@{host}",
            command
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ Команда выполнена успешно")
            if result.stdout.strip():
                print(f"📤 Вывод: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Ошибка выполнения команды: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Таймаут выполнения команды")
        return False
    except FileNotFoundError:
        print("❌ sshpass не установлен. Установите: sudo apt install sshpass")
        return False
    except Exception as e:
        print(f"❌ Ошибка SSH: {e}")
        return False

def copy_files_to_server(host: str, username: str, password: str, local_path: str, remote_path: str) -> bool:
    """Копирует файлы на сервер"""
    try:
        cmd = [
            "sshpass", "-p", password,
            "rsync", "-avz", "--progress",
            "--exclude=.git",
            "--exclude=__pycache__",
            "--exclude=*.pyc",
            "--exclude=.env",
            "--exclude=uploads/",
            "--exclude=outputs/",
            "--exclude=logs/",
            f"{local_path}/",
            f"{username}@{host}:{remote_path}/"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print(f"✅ Файлы скопированы успешно")
            return True
        else:
            print(f"❌ Ошибка копирования файлов: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Таймаут копирования файлов")
        return False
    except FileNotFoundError:
        print("❌ rsync не установлен. Установите: sudo apt install rsync")
        return False
    except Exception as e:
        print(f"❌ Ошибка копирования: {e}")
        return False

def check_server_connection(host: str, username: str, password: str) -> bool:
    """Проверяет соединение с сервером"""
    print(f"🔍 Проверяем соединение с сервером {host}...")
    return run_ssh_command(host, username, password, "echo 'Connection successful'")

def deploy_to_server(config: Dict[str, Any]) -> bool:
    """Основная функция развертывания"""
    server_config = config["server"]
    deployment_config = config["deployment"]
    
    host = server_config["host"]
    username = server_config["username"]
    password = server_config["password"]
    app_name = deployment_config["app_name"]
    
    print(f"🚀 Начинаем развертывание {app_name} на {host}")
    
    # Проверяем соединение
    if not check_server_connection(host, username, password):
        return False
    
    # Копируем скрипт развертывания
    print("📋 Копируем скрипт развертывания...")
    if not copy_files_to_server(host, username, password, "scripts/deploy_debian.sh", "/tmp/"):
        return False
    
    # Выполняем скрипт развертывания
    print("🔧 Выполняем скрипт развертывания...")
    if not run_ssh_command(host, username, password, "chmod +x /tmp/deploy_debian.sh && /tmp/deploy_debian.sh"):
        return False
    
    # Копируем файлы проекта
    print("📁 Копируем файлы проекта...")
    if not copy_files_to_server(host, username, password, ".", f"/opt/{app_name}"):
        return False
    
    # Запускаем сервис
    print("▶️ Запускаем сервис...")
    if not run_ssh_command(host, username, password, f"systemctl start {app_name}.service"):
        return False
    
    # Ждем запуска
    print("⏳ Ждем запуска сервиса...")
    time.sleep(10)
    
    # Проверяем статус
    print("🔍 Проверяем статус сервиса...")
    if not run_ssh_command(host, username, password, f"systemctl status {app_name}.service --no-pager"):
        return False
    
    # Проверяем доступность API
    print("🌐 Проверяем доступность API...")
    if not run_ssh_command(host, username, password, f"curl -f http://localhost:{deployment_config['app_port']}/health"):
        print("⚠️ API может быть недоступен, но сервис запущен")
    
    print("🎉 Развертывание завершено успешно!")
    print(f"🌐 API доступен по адресу: http://{host}:{deployment_config['app_port']}")
    print(f"📚 Документация API: http://{host}:{deployment_config['app_port']}/docs")
    
    return True

def main():
    """Главная функция"""
    print("🐍 Python API Server Deployer")
    print("=" * 40)
    
    # Проверяем наличие конфигурационного файла
    config_path = "server_config.json"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    if not os.path.exists(config_path):
        print(f"❌ Конфигурационный файл {config_path} не найден")
        print("💡 Создайте файл server_config.json с настройками сервера")
        sys.exit(1)
    
    # Загружаем конфигурацию
    config = load_config(config_path)
    
    # Проверяем необходимые поля
    required_fields = ["server.host", "server.username", "server.password", "deployment.app_name"]
    for field in required_fields:
        keys = field.split(".")
        current = config
        for key in keys:
            if key not in current:
                print(f"❌ Отсутствует поле {field} в конфигурации")
                sys.exit(1)
            current = current[key]
    
    # Выполняем развертывание
    try:
        success = deploy_to_server(config)
        if success:
            print("\n✅ Развертывание завершено успешно!")
            sys.exit(0)
        else:
            print("\n❌ Развертывание завершилось с ошибками")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Развертывание прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
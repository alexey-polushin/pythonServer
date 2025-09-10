#!/usr/bin/env python3
"""
Скрипт для обновления кода на сервере
"""

import json
import os
import subprocess
import sys
import time
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
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

def run_ssh_command(host: str, username: str, auth_method: str, password: str = None, ssh_key_path: str = None, command: str = "") -> bool:
    """Выполняет команду по SSH"""
    try:
        if auth_method == "ssh_key" and ssh_key_path:
            # Используем SSH ключ
            expanded_key_path = os.path.expanduser(ssh_key_path)
            cmd = [
                "ssh", "-i", expanded_key_path,
                "-o", "StrictHostKeyChecking=no",
                f"{username}@{host}",
                command
            ]
        elif auth_method == "password":
            # Используем пароль через sshpass
            if not password:
                print("❌ Пароль не указан для аутентификации по паролю")
                return False
            cmd = [
                "sshpass", "-p", password,
                "ssh", "-o", "StrictHostKeyChecking=no",
                f"{username}@{host}",
                command
            ]
        else:
            print("❌ Неверный метод аутентификации или отсутствуют необходимые параметры")
            return False
        
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
    except Exception as e:
        print(f"❌ Ошибка SSH: {e}")
        return False

def copy_files_to_server(host: str, username: str, auth_method: str, password: str = None, ssh_key_path: str = None, local_path: str = "", remote_path: str = "") -> bool:
    """Копирует файлы на сервер"""
    try:
        if auth_method == "ssh_key" and ssh_key_path:
            # Используем SSH ключ
            expanded_key_path = os.path.expanduser(ssh_key_path)
            cmd = [
                "rsync", "-avz", "--progress",
                "-e", f"ssh -i {expanded_key_path} -o StrictHostKeyChecking=no",
                "--exclude=.git",
                "--exclude=__pycache__",
                "--exclude='*.pyc'",
                "--exclude=.env",
                "--exclude=uploads/",
                "--exclude=outputs/",
                "--exclude=logs/",
                f"{local_path}/",
                f"{username}@{host}:{remote_path}/"
            ]
        else:
            # Используем пароль через sshpass
            if not password:
                print("❌ Пароль не указан для аутентификации по паролю")
                return False
            cmd = [
                "sshpass", "-p", password,
                "rsync", "-avz", "--progress",
                "-e", "ssh -o StrictHostKeyChecking=no",
                "--exclude=.git",
                "--exclude=__pycache__",
                "--exclude='*.pyc'",
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
        print("❌ rsync не установлен. Установите: brew install rsync")
        return False
    except Exception as e:
        print(f"❌ Ошибка копирования: {e}")
        return False

def update_server(config: Dict[str, Any]) -> bool:
    """Обновляет код на сервере"""
    server_config = config["server"]
    deployment_config = config.get("deployment", {})
    
    host = server_config["host"]
    username = server_config["username"]
    auth_method = server_config.get("auth_method", "password")
    password = server_config.get("password")
    ssh_key_path = server_config.get("ssh_key_path")
    app_name = deployment_config.get("app_name", "dive-color-corrector")
    
    print(f"🔄 Обновляем {app_name} на {host}")
    print(f"🔐 Метод аутентификации: {auth_method}")
    
    # Копируем новый код
    print("📁 Копируем новый код...")
    if not copy_files_to_server(host, username, auth_method, password, ssh_key_path, ".", f"/opt/{app_name}"):
        return False
    
    # Подготавливаем Docker файлы
    print("🐳 Подготавливаем Docker файлы...")
    if not run_ssh_command(host, username, auth_method, password, ssh_key_path, f"cd /opt/{app_name} && mkdir -p nginx && cp docker/nginx/nginx.conf nginx/"):
        return False
    
    # Запускаем скрипт обновления на сервере
    print("🔄 Запускаем обновление на сервере...")
    if not run_ssh_command(host, username, auth_method, password, ssh_key_path, f"cd /opt/{app_name} && chmod +x update.sh && ./update.sh"):
        return False
    
    # Проверяем статус
    print("🔍 Проверяем статус после обновления...")
    time.sleep(10)
    if not run_ssh_command(host, username, auth_method, password, ssh_key_path, f"curl -f http://localhost/health"):
        print("⚠️ API может быть недоступен после обновления")
        return False
    
    print("🎉 Обновление завершено успешно!")
    print(f"🌐 API доступен по адресу: http://{host}")
    print(f"📚 Документация API: http://{host}/docs")
    print(f"📱 Мобильный API: http://{host}/api/mobile/status")
    
    return True

def main():
    """Главная функция"""
    print("🔄 Python API Server Updater")
    print("=" * 50)
    
    # Проверяем наличие конфигурационного файла
    config_path = "server_config.json"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    if not os.path.exists(config_path):
        print(f"❌ Конфигурационный файл {config_path} не найден")
        print("💡 Создайте файл server_config.json на основе server_config.example.json")
        sys.exit(1)
    
    # Загружаем конфигурацию
    config = load_config(config_path)
    
    # Проверяем необходимые поля
    required_fields = ["server.host", "server.username", "server.password"]
    for field in required_fields:
        keys = field.split(".")
        current = config
        for key in keys:
            if key not in current:
                print(f"❌ Отсутствует поле {field} в конфигурации")
                sys.exit(1)
            current = current[key]
    
    # Обновляем сервер
    if update_server(config):
        print("✅ Обновление завершено успешно!")
    else:
        print("❌ Обновление завершилось с ошибками")
        sys.exit(1)

if __name__ == "__main__":
    main()

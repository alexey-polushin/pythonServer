#!/usr/bin/env python3
"""
Скрипт для настройки профилей качества видео
"""

import sys
import os
import json
import argparse

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dive_color_corrector.mobile_correct import configure_performance, get_performance_info

def load_quality_profiles():
    """Загружает профили качества из файла"""
    profiles_path = os.path.join(os.path.dirname(__file__), '..', 'quality_profiles.json')
    try:
        with open(profiles_path, 'r', encoding='utf-8') as f:
            return json.load(f)['quality_profiles']
    except FileNotFoundError:
        print("❌ Файл quality_profiles.json не найден")
        return {}
    except json.JSONDecodeError:
        print("❌ Ошибка в формате файла quality_profiles.json")
        return {}

def list_profiles():
    """Показывает доступные профили"""
    profiles = load_quality_profiles()
    if not profiles:
        return
    
    print("📋 Доступные профили качества:")
    print()
    
    for key, profile in profiles.items():
        print(f"🎯 {profile['name']} ({key})")
        print(f"   Описание: {profile['description']}")
        print(f"   Качество: {profile['video_quality']}%")
        print(f"   Ожидаемый размер: {profile['expected_size_ratio']}x от оригинала")
        print(f"   Применение: {', '.join(profile['use_cases'])}")
        print()

def apply_profile(profile_key):
    """Применяет профиль качества"""
    profiles = load_quality_profiles()
    if profile_key not in profiles:
        print(f"❌ Профиль '{profile_key}' не найден")
        return False
    
    profile = profiles[profile_key]
    
    print(f"🎯 Применяем профиль: {profile['name']}")
    print(f"   Качество: {profile['video_quality']}%")
    print(f"   Batch size: {profile['batch_size']}")
    print(f"   Процессы: {profile['max_processes']}")
    print(f"   GPU: {'Включен' if profile['use_gpu'] else 'Выключен'}")
    print()
    
    try:
        configure_performance(
            batch_size=profile['batch_size'],
            max_processes=profile['max_processes'],
            video_quality=profile['video_quality'],
            use_gpu=profile['use_gpu']
        )
        
        print("✅ Профиль успешно применен!")
        
        # Показываем текущие настройки
        current = get_performance_info()
        print()
        print("📊 Текущие настройки:")
        print(f"   • Качество видео: {current['video_quality']}%")
        print(f"   • Batch size: {current['batch_size']}")
        print(f"   • Процессы: {current['max_processes']}")
        print(f"   • GPU: {'Включен' if current['use_gpu'] else 'Выключен'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при применении профиля: {str(e)}")
        return False

def show_current():
    """Показывает текущие настройки"""
    try:
        current = get_performance_info()
        print("📊 Текущие настройки качества:")
        print(f"   • Качество видео: {current['video_quality']}%")
        print(f"   • Batch size: {current['batch_size']}")
        print(f"   • Процессы: {current['max_processes']}")
        print(f"   • GPU: {'Включен' if current['use_gpu'] else 'Выключен'}")
        print(f"   • Тип GPU: {current.get('gpu_type', 'Не определен')}")
    except Exception as e:
        print(f"❌ Ошибка при получении настроек: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Настройка профилей качества видео')
    parser.add_argument('action', nargs='?', choices=['list', 'current', 'set'], 
                       help='Действие: list (список), current (текущие), set (установить)')
    parser.add_argument('profile', nargs='?', help='Название профиля для установки')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        list_profiles()
    elif args.action == 'current':
        show_current()
    elif args.action == 'set':
        if not args.profile:
            print("❌ Укажите название профиля")
            print("Используйте: python set_quality_profile.py list - для просмотра доступных профилей")
            return
        apply_profile(args.profile)
    else:
        print("🎯 Настройка профилей качества видео")
        print()
        print("Использование:")
        print("  python set_quality_profile.py list     - показать доступные профили")
        print("  python set_quality_profile.py current  - показать текущие настройки")
        print("  python set_quality_profile.py set <профиль> - применить профиль")
        print()
        print("Примеры:")
        print("  python set_quality_profile.py set high_quality")
        print("  python set_quality_profile.py set balanced")
        print("  python set_quality_profile.py set optimized")

if __name__ == "__main__":
    main()

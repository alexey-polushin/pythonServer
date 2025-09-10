#!/usr/bin/env python3
"""
Скрипт для переключения профилей конфигурации
"""

import json
import sys
import os

def load_profiles():
    """Загружает профили конфигурации"""
    profiles_file = os.path.join(os.path.dirname(__file__), '..', 'config_profiles.json')
    with open(profiles_file, 'r') as f:
        return json.load(f)

def apply_profile(profile_name):
    """Применяет профиль конфигурации"""
    profiles = load_profiles()
    
    if profile_name not in profiles['profiles']:
        print(f"❌ Профиль '{profile_name}' не найден")
        print(f"Доступные профили: {', '.join(profiles['profiles'].keys())}")
        return False
    
    profile = profiles['profiles'][profile_name]
    config = profile['config']
    
    # Применяем конфигурацию
    sys.path.append('src')
    from dive_color_corrector.mobile_correct import configure_performance
    
    configure_performance(
        batch_size=config['batch_size'],
        max_processes=config['max_processes'],
        video_quality=config['video_quality'],
        use_gpu=config['use_gpu']
    )
    
    # Сохраняем в файл конфигурации
    config_file = "performance_config.json"
    with open(config_file, 'w') as f:
        json.dump({
            "batch_size": config['batch_size'],
            "max_processes": config['max_processes'],
            "video_quality": config['video_quality'],
            "use_gpu": config['use_gpu'],
            "profile": profile_name,
            "auto_configure": False
        }, f, indent=2)
    
    print(f"✅ Профиль '{profile_name}' применен:")
    print(f"  • Название: {profile['name']}")
    print(f"  • Описание: {profile['description']}")
    print(f"  • Использование: {profile['use_case']}")
    print(f"  • batch_size: {config['batch_size']}")
    print(f"  • max_processes: {config['max_processes']}")
    print(f"  • video_quality: {config['video_quality']}")
    print(f"  • use_gpu: {config['use_gpu']}")
    
    return True

def list_profiles():
    """Показывает список доступных профилей"""
    profiles = load_profiles()
    
    print("📋 Доступные профили конфигурации:")
    print("=" * 60)
    
    for key, profile in profiles['profiles'].items():
        print(f"🔧 {key}")
        print(f"   Название: {profile['name']}")
        print(f"   Описание: {profile['description']}")
        print(f"   Использование: {profile['use_case']}")
        print(f"   Конфигурация: batch_size={profile['config']['batch_size']}, "
              f"max_processes={profile['config']['max_processes']}, "
              f"quality={profile['config']['video_quality']}")
        print()

def get_recommendation():
    """Получает рекомендацию профиля для текущей системы"""
    import multiprocessing as mp
    import psutil
    
    cpu_count = mp.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    profiles = load_profiles()
    recommendations = profiles['recommendations']
    
    print(f"💡 Рекомендации для вашей системы:")
    print(f"  • CPU ядер: {cpu_count}")
    print(f"  • RAM: {memory_gb:.1f} GB")
    print()
    
    # Определяем подходящий профиль
    if cpu_count >= 8 and memory_gb >= 16:
        recommended = "8_cores_16gb"
    elif cpu_count >= 4 and memory_gb >= 8:
        recommended = "4_cores_8gb"
    else:
        recommended = "2_cores_4gb"
    
    recommendation = recommendations[recommended]
    profile_name = recommendation['profile']
    reason = recommendation['reason']
    
    print(f"🎯 Рекомендуемый профиль: {profile_name}")
    print(f"   Причина: {reason}")
    print()
    
    # Показываем детали профиля
    profile = profiles['profiles'][profile_name]
    print(f"📊 Детали профиля:")
    print(f"   • Название: {profile['name']}")
    print(f"   • Описание: {profile['description']}")
    print(f"   • batch_size: {profile['config']['batch_size']}")
    print(f"   • max_processes: {profile['config']['max_processes']}")
    print(f"   • video_quality: {profile['config']['video_quality']}")
    print(f"   • use_gpu: {profile['config']['use_gpu']}")
    
    return profile_name

def main():
    """Основная функция"""
    import argparse
    parser = argparse.ArgumentParser(description='Switch performance profiles')
    parser.add_argument('profile', nargs='?', help='Profile name to apply')
    parser.add_argument('--list', action='store_true', help='List available profiles')
    parser.add_argument('--recommend', action='store_true', help='Get recommendation for current system')
    parser.add_argument('--auto', action='store_true', help='Apply recommended profile automatically')
    
    args = parser.parse_args()
    
    if args.list:
        list_profiles()
    elif args.recommend:
        get_recommendation()
    elif args.auto:
        recommended = get_recommendation()
        apply_profile(recommended)
    elif args.profile:
        apply_profile(args.profile)
    else:
        print("🔧 Управление профилями производительности")
        print()
        print("Использование:")
        print("  python scripts/switch_profile.py <profile_name>  # Применить профиль")
        print("  python scripts/switch_profile.py --list          # Показать профили")
        print("  python scripts/switch_profile.py --recommend     # Получить рекомендацию")
        print("  python scripts/switch_profile.py --auto          # Применить рекомендуемый")
        print()
        get_recommendation()

if __name__ == "__main__":
    main()

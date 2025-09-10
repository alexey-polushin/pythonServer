#!/usr/bin/env python3
"""
Оптимизатор настроек производительности для удаленного сервера
"""

import sys
import os
import json
import time
import psutil
import argparse
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dive_color_corrector.mobile_correct import configure_performance, get_performance_info

def detect_server_characteristics():
    """Определяет характеристики удаленного сервера"""
    print("🔍 Анализируем характеристики сервера...")
    
    # CPU информация
    cpu_count = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    cpu_usage = psutil.cpu_percent(interval=1)
    
    # Память
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    # Диск
    disk = psutil.disk_usage('/')
    
    # GPU (проверяем доступность)
    gpu_available = False
    gpu_type = None
    
    try:
        import torch
        if torch.backends.mps.is_available() and torch.backends.mps.is_built():
            gpu_available = True
            gpu_type = "MPS"
        elif torch.cuda.is_available():
            gpu_available = True
            gpu_type = "CUDA"
    except ImportError:
        pass
    
    # Проверяем CuPy
    if not gpu_available:
        try:
            import cupy as cp
            gpu_available = True
            gpu_type = "CUDA"
        except ImportError:
            pass
    
    characteristics = {
        "cpu": {
            "cores": cpu_count,
            "frequency_mhz": cpu_freq.max if cpu_freq else 0,
            "usage_percent": cpu_usage
        },
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "usage_percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "usage_percent": round((disk.used / disk.total) * 100, 2)
        },
        "gpu": {
            "available": gpu_available,
            "type": gpu_type
        }
    }
    
    return characteristics

def recommend_optimal_settings(characteristics):
    """Рекомендует оптимальные настройки на основе характеристик сервера"""
    print("🎯 Определяем оптимальные настройки...")
    
    cpu_cores = characteristics["cpu"]["cores"]
    memory_gb = characteristics["memory"]["total_gb"]
    gpu_available = characteristics["gpu"]["available"]
    gpu_type = characteristics["gpu"]["type"]
    
    # Определяем профиль сервера
    if cpu_cores >= 16 and memory_gb >= 32:
        server_profile = "high_end"
    elif cpu_cores >= 8 and memory_gb >= 16:
        server_profile = "mid_range"
    elif cpu_cores >= 4 and memory_gb >= 8:
        server_profile = "standard"
    else:
        server_profile = "low_end"
    
    # Рекомендуемые настройки
    if server_profile == "high_end":
        settings = {
            "batch_size": 128,
            "max_processes": min(cpu_cores, 16),
            "video_quality": 90,
            "use_gpu": gpu_available,
            "profile": "high_end"
        }
    elif server_profile == "mid_range":
        settings = {
            "batch_size": 64,
            "max_processes": min(cpu_cores, 8),
            "video_quality": 85,
            "use_gpu": gpu_available,
            "profile": "mid_range"
        }
    elif server_profile == "standard":
        settings = {
            "batch_size": 32,
            "max_processes": min(cpu_cores, 4),
            "video_quality": 80,
            "use_gpu": gpu_available,
            "profile": "standard"
        }
    else:  # low_end
        settings = {
            "batch_size": 16,
            "max_processes": min(cpu_cores, 2),
            "video_quality": 75,
            "use_gpu": False,  # Отключаем GPU для слабых серверов
            "profile": "low_end"
        }
    
    return settings, server_profile

def test_performance_settings(settings, test_video_path="tests/sample.mp4"):
    """Тестирует производительность с рекомендуемыми настройками"""
    print("⚡ Тестируем производительность...")
    
    if not os.path.exists(test_video_path):
        print(f"⚠️ Тестовое видео не найдено: {test_video_path}")
        return None
    
    try:
        # Применяем настройки
        configure_performance(
            batch_size=settings["batch_size"],
            max_processes=settings["max_processes"],
            video_quality=settings["video_quality"],
            use_gpu=settings["use_gpu"]
        )
        
        # Импортируем функции обработки
        from dive_color_corrector.mobile_correct import analyze_video_mobile
        
        # Тестируем
        output_path = "tests/remote_optimization_test.mp4"
        start_time = time.time()
        
        video_data = analyze_video_mobile(test_video_path, output_path)
        
        total_time = time.time() - start_time
        
        # Анализируем результаты
        if os.path.exists(output_path):
            original_size = os.path.getsize(test_video_path)
            output_size = os.path.getsize(output_path)
            
            results = {
                "total_time": total_time,
                "fps_achieved": video_data.get("frame_count", 0) / total_time if total_time > 0 else 0,
                "size_ratio": output_size / original_size if original_size > 0 else 0,
                "success": True
            }
        else:
            results = {"success": False, "error": "Output file not created"}
        
        return results
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def save_server_config(characteristics, settings, test_results):
    """Сохраняет конфигурацию сервера"""
    config = {
        "server_characteristics": characteristics,
        "optimal_settings": settings,
        "test_results": test_results,
        "optimization_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "server_id": f"{characteristics['cpu']['cores']}c_{characteristics['memory']['total_gb']}gb_{characteristics['gpu']['type'] or 'cpu'}"
    }
    
    config_path = "server_optimization_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    return config_path

def print_optimization_report(characteristics, settings, server_profile, test_results):
    """Выводит отчет об оптимизации"""
    print("\n" + "="*60)
    print("🚀 ОТЧЕТ ОБ ОПТИМИЗАЦИИ УДАЛЕННОГО СЕРВЕРА")
    print("="*60)
    
    print(f"\n📊 Характеристики сервера:")
    print(f"   • CPU ядер: {characteristics['cpu']['cores']}")
    print(f"   • Частота CPU: {characteristics['cpu']['frequency_mhz']} MHz")
    print(f"   • Память: {characteristics['memory']['total_gb']} GB")
    print(f"   • Диск: {characteristics['disk']['total_gb']} GB")
    print(f"   • GPU: {'✅ ' + characteristics['gpu']['type'] if characteristics['gpu']['available'] else '❌ Недоступен'}")
    
    print(f"\n🎯 Профиль сервера: {server_profile.upper()}")
    
    print(f"\n⚙️ Рекомендуемые настройки:")
    print(f"   • Batch size: {settings['batch_size']}")
    print(f"   • Процессы: {settings['max_processes']}")
    print(f"   • Качество видео: {settings['video_quality']}%")
    print(f"   • GPU: {'Включен' if settings['use_gpu'] else 'Выключен'}")
    
    if test_results and test_results.get('success'):
        print(f"\n📈 Результаты тестирования:")
        print(f"   • Время обработки: {test_results['total_time']:.2f} сек")
        print(f"   • FPS: {test_results['fps_achieved']:.2f}")
        print(f"   • Соотношение размеров: {test_results['size_ratio']:.2f}x")
    elif test_results:
        print(f"\n⚠️ Ошибка тестирования: {test_results.get('error', 'Неизвестная ошибка')}")
    
    print(f"\n✅ Настройки применены и сохранены!")

def main():
    parser = argparse.ArgumentParser(description='Оптимизация настроек для удаленного сервера')
    parser.add_argument('--test-video', default='tests/sample.mp4', 
                       help='Путь к тестовому видео')
    parser.add_argument('--skip-test', action='store_true',
                       help='Пропустить тестирование производительности')
    parser.add_argument('--force-profile', choices=['high_end', 'mid_range', 'standard', 'low_end'],
                       help='Принудительно установить профиль сервера')
    
    args = parser.parse_args()
    
    print("🚀 Оптимизатор настроек удаленного сервера")
    print("="*50)
    
    # 1. Определяем характеристики сервера
    characteristics = detect_server_characteristics()
    
    # 2. Рекомендуем оптимальные настройки
    settings, server_profile = recommend_optimal_settings(characteristics)
    
    # Принудительный профиль
    if args.force_profile:
        settings["profile"] = args.force_profile
        server_profile = args.force_profile
        print(f"🔧 Принудительно установлен профиль: {args.force_profile}")
    
    # 3. Применяем оптимальные настройки
    print("⚙️ Применяем оптимальные настройки...")
    configure_performance(
        batch_size=settings["batch_size"],
        max_processes=settings["max_processes"],
        video_quality=settings["video_quality"],
        use_gpu=settings["use_gpu"]
    )
    
    # 4. Тестируем производительность (если не пропущено)
    test_results = None
    if not args.skip_test:
        test_results = test_performance_settings(settings, args.test_video)
    
    # 5. Сохраняем конфигурацию
    config_path = save_server_config(characteristics, settings, test_results)
    
    # 5. Выводим отчет
    print_optimization_report(characteristics, settings, server_profile, test_results)
    
    print(f"\n💾 Конфигурация сохранена в: {config_path}")
    print("\n🎉 Оптимизация завершена!")

if __name__ == "__main__":
    main()

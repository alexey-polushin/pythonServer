#!/usr/bin/env python3
"""
Мониторинг производительности удаленного сервера в реальном времени
"""

import sys
import os
import time
import psutil
import json
import argparse
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dive_color_corrector.mobile_correct import get_performance_info

class PerformanceMonitor:
    def __init__(self, log_file=None):
        self.log_file = log_file
        self.start_time = time.time()
        self.monitoring = False
        
    def get_system_stats(self):
        """Получает текущую статистику системы"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        
        # Память
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Диск
        disk = psutil.disk_usage('/')
        
        # Сеть
        network = psutil.net_io_counters()
        
        # Процессы
        processes = len(psutil.pids())
        
        # GPU (если доступен)
        gpu_usage = None
        try:
            import torch
            if torch.backends.mps.is_available():
                # Для MPS нет прямого способа получить использование
                gpu_usage = "MPS Available"
            elif torch.cuda.is_available():
                gpu_usage = f"CUDA: {torch.cuda.memory_allocated() / 1024**3:.2f}GB"
        except ImportError:
            pass
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - self.start_time,
            "cpu": {
                "usage_percent": cpu_percent,
                "frequency_mhz": cpu_freq.current if cpu_freq else 0,
                "cores": psutil.cpu_count(logical=True)
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent
            },
            "swap": {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "usage_percent": swap.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "usage_percent": round((disk.used / disk.total) * 100, 2)
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            "processes": processes,
            "gpu": gpu_usage
        }
    
    def get_video_processing_stats(self):
        """Получает статистику обработки видео"""
        try:
            perf_info = get_performance_info()
            return {
                "video_quality": perf_info.get("video_quality", 0),
                "batch_size": perf_info.get("batch_size", 0),
                "max_processes": perf_info.get("max_processes", 0),
                "use_gpu": perf_info.get("use_gpu", False),
                "gpu_type": perf_info.get("gpu_type", "None")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def log_stats(self, stats):
        """Логирует статистику в файл"""
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(stats) + '\n')
    
    def print_stats(self, stats, video_stats):
        """Выводит статистику в консоль"""
        # Очищаем экран
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🖥️  МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ СЕРВЕРА")
        print("=" * 60)
        print(f"⏰ Время: {stats['timestamp']}")
        print(f"⏱️  Время работы: {stats['uptime']:.0f} сек")
        print()
        
        # CPU
        cpu_color = "🟢" if stats['cpu']['usage_percent'] < 70 else "🟡" if stats['cpu']['usage_percent'] < 90 else "🔴"
        print(f"{cpu_color} CPU: {stats['cpu']['usage_percent']:.1f}% ({stats['cpu']['cores']} ядер, {stats['cpu']['frequency_mhz']:.0f} MHz)")
        
        # Память
        mem_color = "🟢" if stats['memory']['usage_percent'] < 70 else "🟡" if stats['memory']['usage_percent'] < 90 else "🔴"
        print(f"{mem_color} Память: {stats['memory']['usage_percent']:.1f}% ({stats['memory']['used_gb']:.1f}/{stats['memory']['total_gb']:.1f} GB)")
        
        # Диск
        disk_color = "🟢" if stats['disk']['usage_percent'] < 70 else "🟡" if stats['disk']['usage_percent'] < 90 else "🔴"
        print(f"{disk_color} Диск: {stats['disk']['usage_percent']:.1f}% ({stats['disk']['used_gb']:.1f}/{stats['disk']['total_gb']:.1f} GB)")
        
        # Swap
        if stats['swap']['total_gb'] > 0:
            swap_color = "🟢" if stats['swap']['usage_percent'] < 10 else "🟡" if stats['swap']['usage_percent'] < 30 else "🔴"
            print(f"{swap_color} Swap: {stats['swap']['usage_percent']:.1f}% ({stats['swap']['used_gb']:.1f}/{stats['swap']['total_gb']:.1f} GB)")
        
        # Процессы
        print(f"📊 Процессы: {stats['processes']}")
        
        # GPU
        if stats['gpu']:
            print(f"🎮 GPU: {stats['gpu']}")
        
        print()
        print("🎬 НАСТРОЙКИ ОБРАБОТКИ ВИДЕО:")
        if 'error' not in video_stats:
            print(f"   • Качество: {video_stats.get('video_quality', 0)}%")
            print(f"   • Batch size: {video_stats.get('batch_size', 0)}")
            print(f"   • Процессы: {video_stats.get('max_processes', 0)}")
            print(f"   • GPU: {'Включен' if video_stats.get('use_gpu') else 'Выключен'}")
            if video_stats.get('gpu_type'):
                print(f"   • Тип GPU: {video_stats.get('gpu_type')}")
        else:
            print(f"   ❌ Ошибка: {video_stats['error']}")
        
        print()
        print("📈 СЕТЬ:")
        print(f"   • Отправлено: {stats['network']['bytes_sent'] / 1024 / 1024:.1f} MB")
        print(f"   • Получено: {stats['network']['bytes_recv'] / 1024 / 1024:.1f} MB")
        
        print()
        print("💡 Нажмите Ctrl+C для остановки мониторинга")
    
    def start_monitoring(self, interval=2):
        """Запускает мониторинг"""
        self.monitoring = True
        print("🚀 Запуск мониторинга производительности...")
        print("Нажмите Ctrl+C для остановки")
        
        try:
            while self.monitoring:
                stats = self.get_system_stats()
                video_stats = self.get_video_processing_stats()
                
                self.print_stats(stats, video_stats)
                self.log_stats({**stats, "video_processing": video_stats})
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Мониторинг остановлен")
            self.monitoring = False

def main():
    parser = argparse.ArgumentParser(description='Мониторинг производительности сервера')
    parser.add_argument('--interval', type=int, default=2,
                       help='Интервал обновления в секундах (по умолчанию: 2)')
    parser.add_argument('--log-file', 
                       help='Файл для логирования статистики')
    parser.add_argument('--once', action='store_true',
                       help='Показать статистику один раз и выйти')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(log_file=args.log_file)
    
    if args.once:
        # Показать статистику один раз
        stats = monitor.get_system_stats()
        video_stats = monitor.get_video_processing_stats()
        monitor.print_stats(stats, video_stats)
    else:
        # Непрерывный мониторинг
        monitor.start_monitoring(interval=args.interval)

if __name__ == "__main__":
    main()

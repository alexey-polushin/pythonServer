#!/usr/bin/env python3
"""
Настройка очереди обработки видео для высоких нагрузок
"""

import asyncio
import aiofiles
import json
import os
from datetime import datetime
from typing import List, Dict, Any

class VideoProcessingQueue:
    """Очередь обработки видео"""
    
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.queue_file = "video_queue.json"
        self.processing_file = "processing_status.json"
        self.completed_file = "completed_videos.json"
        
    async def add_to_queue(self, video_path: str, priority: int = 1) -> str:
        """Добавляет видео в очередь"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(video_path) % 10000}"
        
        task = {
            "id": task_id,
            "video_path": video_path,
            "priority": priority,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None
        }
        
        # Загружаем текущую очередь
        queue = await self._load_queue()
        queue.append(task)
        
        # Сортируем по приоритету
        queue.sort(key=lambda x: x['priority'], reverse=True)
        
        # Сохраняем очередь
        await self._save_queue(queue)
        
        print(f"✅ Видео добавлено в очередь: {task_id}")
        return task_id
    
    async def process_queue(self):
        """Обрабатывает очередь видео"""
        print(f"🚀 Запуск обработки очереди (макс. {self.max_concurrent} параллельно)...")
        
        while True:
            queue = await self._load_queue()
            processing = await self._load_processing()
            
            # Находим задачи для обработки
            queued_tasks = [t for t in queue if t['status'] == 'queued']
            active_tasks = [t for t in processing if t['status'] == 'processing']
            
            # Запускаем новые задачи если есть свободные слоты
            available_slots = self.max_concurrent - len(active_tasks)
            
            for task in queued_tasks[:available_slots]:
                await self._start_processing(task)
            
            # Проверяем завершенные задачи
            await self._check_completed_tasks()
            
            if not queued_tasks and not active_tasks:
                print("✅ Очередь пуста, ожидание новых задач...")
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(2)
    
    async def _start_processing(self, task: Dict[str, Any]):
        """Запускает обработку задачи"""
        task['status'] = 'processing'
        task['started_at'] = datetime.now().isoformat()
        
        # Перемещаем в processing
        processing = await self._load_processing()
        processing.append(task)
        await self._save_processing(processing)
        
        # Удаляем из очереди
        queue = await self._load_queue()
        queue = [t for t in queue if t['id'] != task['id']]
        await self._save_queue(queue)
        
        # Запускаем обработку в фоне
        asyncio.create_task(self._process_video(task))
        
        print(f"🎬 Начата обработка: {task['id']}")
    
    async def _process_video(self, task: Dict[str, Any]):
        """Обрабатывает видео"""
        try:
            import sys
            sys.path.append('src')
            from dive_color_corrector.mobile_correct import analyze_video_mobile, process_video_mobile
            
            # Генерируем путь для выходного файла
            input_path = task['video_path']
            output_path = input_path.replace('.mp4', '_processed.mp4')
            
            # Анализируем видео
            video_data = analyze_video_mobile(input_path, output_path)
            
            # Обрабатываем видео
            result = process_video_mobile(video_data)
            
            # Обновляем статус
            task['status'] = 'completed'
            task['completed_at'] = datetime.now().isoformat()
            task['output_path'] = output_path
            task['result'] = result
            
            # Перемещаем в completed
            completed = await self._load_completed()
            completed.append(task)
            await self._save_completed(completed)
            
            # Удаляем из processing
            processing = await self._load_processing()
            processing = [t for t in processing if t['id'] != task['id']]
            await self._save_processing(processing)
            
            print(f"✅ Обработка завершена: {task['id']}")
            
        except Exception as e:
            # Обрабатываем ошибку
            task['status'] = 'error'
            task['error'] = str(e)
            task['completed_at'] = datetime.now().isoformat()
            
            # Перемещаем в completed с ошибкой
            completed = await self._load_completed()
            completed.append(task)
            await self._save_completed(completed)
            
            # Удаляем из processing
            processing = await self._load_processing()
            processing = [t for t in processing if t['id'] != task['id']]
            await self._save_processing(processing)
            
            print(f"❌ Ошибка обработки {task['id']}: {str(e)}")
    
    async def _check_completed_tasks(self):
        """Проверяет завершенные задачи"""
        # Здесь можно добавить логику для очистки старых задач
        pass
    
    async def _load_queue(self) -> List[Dict[str, Any]]:
        """Загружает очередь"""
        if os.path.exists(self.queue_file):
            async with aiofiles.open(self.queue_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        return []
    
    async def _save_queue(self, queue: List[Dict[str, Any]]):
        """Сохраняет очередь"""
        async with aiofiles.open(self.queue_file, 'w') as f:
            await f.write(json.dumps(queue, indent=2))
    
    async def _load_processing(self) -> List[Dict[str, Any]]:
        """Загружает список обрабатываемых задач"""
        if os.path.exists(self.processing_file):
            async with aiofiles.open(self.processing_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        return []
    
    async def _save_processing(self, processing: List[Dict[str, Any]]):
        """Сохраняет список обрабатываемых задач"""
        async with aiofiles.open(self.processing_file, 'w') as f:
            await f.write(json.dumps(processing, indent=2))
    
    async def _load_completed(self) -> List[Dict[str, Any]]:
        """Загружает список завершенных задач"""
        if os.path.exists(self.completed_file):
            async with aiofiles.open(self.completed_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        return []
    
    async def _save_completed(self, completed: List[Dict[str, Any]]):
        """Сохраняет список завершенных задач"""
        async with aiofiles.open(self.completed_file, 'w') as f:
            await f.write(json.dumps(completed, indent=2))
    
    async def get_status(self) -> Dict[str, Any]:
        """Возвращает статус очереди"""
        queue = await self._load_queue()
        processing = await self._load_processing()
        completed = await self._load_completed()
        
        return {
            "queued": len(queue),
            "processing": len(processing),
            "completed": len(completed),
            "queue_tasks": queue,
            "processing_tasks": processing,
            "recent_completed": completed[-10:] if completed else []
        }

async def main():
    """Основная функция"""
    import argparse
    parser = argparse.ArgumentParser(description='Video processing queue')
    parser.add_argument('--add', help='Add video to queue')
    parser.add_argument('--status', action='store_true', help='Show queue status')
    parser.add_argument('--start', action='store_true', help='Start processing queue')
    parser.add_argument('--max-concurrent', type=int, default=3, help='Max concurrent tasks')
    
    args = parser.parse_args()
    
    queue = VideoProcessingQueue(max_concurrent=args.max_concurrent)
    
    if args.add:
        task_id = await queue.add_to_queue(args.add)
        print(f"Task added: {task_id}")
    elif args.status:
        status = await queue.get_status()
        print(f"📊 Статус очереди:")
        print(f"  • В очереди: {status['queued']}")
        print(f"  • Обрабатывается: {status['processing']}")
        print(f"  • Завершено: {status['completed']}")
    elif args.start:
        await queue.process_queue()
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())

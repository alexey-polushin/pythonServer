import os
import tempfile
import uuid
from typing import Optional, Generator, Dict, Any
import cv2
import numpy as np
from fastapi import UploadFile, HTTPException
import logging

from ..dive_color_corrector.mobile_correct import correct_image_mobile, analyze_video_mobile, process_video_mobile

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, upload_dir: str = "uploads", output_dir: str = "outputs"):
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Создает необходимые директории если они не существуют"""
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _get_temp_path(self, filename: str, suffix: str = "") -> str:
        """Генерирует временный путь для файла"""
        unique_id = str(uuid.uuid4())
        name, ext = os.path.splitext(filename)
        return os.path.join(self.upload_dir, f"{unique_id}_{name}{suffix}{ext}")
    
    def _get_output_path(self, filename: str, suffix: str = "_corrected") -> str:
        """Генерирует путь для выходного файла"""
        name, ext = os.path.splitext(filename)
        return os.path.join(self.output_dir, f"{name}{suffix}{ext}")
    
    async def process_image(self, file: UploadFile) -> Dict[str, Any]:
        """Обрабатывает изображение для мобильного API"""
        try:
            # Очищаем все старые файлы перед обработкой нового
            cleaned_files = self.cleanup_all_files()
            logger.info(f"Cleaned {len(cleaned_files)} old files before processing new image")
            
            # Сохраняем загруженный файл
            input_path = self._get_temp_path(file.filename)
            output_path = self._get_output_path(file.filename)
            
            with open(input_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Обрабатываем изображение
            result = correct_image_mobile(input_path, output_path)
            
            # Удаляем временный файл
            os.remove(input_path)
            
            # Добавляем информацию о файле
            result.update({
                "input_filename": file.filename,
                "output_filename": os.path.basename(output_path),
                "file_size": os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                "cleaned_files_count": len(cleaned_files)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    
    async def process_video(self, file: UploadFile) -> Generator[Dict[str, Any], None, None]:
        """Обрабатывает видео для мобильного API с прогрессом"""
        try:
            # Очищаем все старые файлы перед обработкой нового
            cleaned_files = self.cleanup_all_files()
            logger.info(f"Cleaned {len(cleaned_files)} old files before processing new video")
            
            # Сохраняем загруженный файл
            input_path = self._get_temp_path(file.filename)
            output_path = self._get_output_path(file.filename)
            
            with open(input_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Функция для отправки прогресса
            def progress_callback(progress_data):
                yield progress_data
            
            # Анализируем видео
            video_data = analyze_video_mobile(input_path, output_path, progress_callback)
            
            yield {
                "status": "analyzing_complete",
                "total_frames": video_data["frame_count"],
                "fps": video_data["fps"],
                "message": "Video analysis completed, starting processing"
            }
            
            # Обрабатываем видео
            result = process_video_mobile(video_data, progress_callback)
            
            # Удаляем временный файл
            os.remove(input_path)
            
            # Добавляем информацию о файле
            result.update({
                "input_filename": file.filename,
                "output_filename": os.path.basename(output_path),
                "file_size": os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                "cleaned_files_count": len(cleaned_files)
            })
            
            yield result
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Получает информацию о файле"""
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        file_size = os.path.getsize(file_path)
        return {
            "file_path": file_path,
            "file_size": file_size,
            "exists": True
        }
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Удаляет старые файлы"""
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for directory in [self.upload_dir, self.output_dir]:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"Removed old file: {file_path}")
    
    def cleanup_all_files(self):
        """Удаляет все файлы в директориях uploads и outputs"""
        cleaned_files = []
        
        for directory in [self.upload_dir, self.output_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            cleaned_files.append(file_path)
                            logger.info(f"Removed file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error removing file {file_path}: {str(e)}")
        
        return cleaned_files

# Глобальный экземпляр процессора
video_processor = VideoProcessor()

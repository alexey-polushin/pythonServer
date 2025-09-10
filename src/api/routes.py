from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse, FileResponse
import logging
from datetime import datetime
import os
import json

from ..models.schemas import HealthResponse
from ..services.video_processor import video_processor
from ..dive_color_corrector.mobile_correct import configure_performance, get_performance_info
from ..config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

async def check_file_size(file: UploadFile) -> None:
    """Проверка размера загружаемого файла"""
    if hasattr(file, 'size') and file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size allowed: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )


@router.get("/", response_model=HealthResponse)
async def root():
    """Проверка работоспособности сервера"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Детальная проверка здоровья сервера"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.7"
    )






# Video processing endpoints
@router.post("/api/process/image")
async def process_image(file: UploadFile = File(...)):
    """Обработка изображения для коррекции цветов"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        result = await video_processor.process_image(file)
        return result
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/process/video")
async def process_video(file: UploadFile = File(...)):
    """Обработка видео для коррекции цветов (мобильный API)"""
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        async def generate():
            async for result in video_processor.process_video(file):
                yield f"data: {json.dumps(result)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache", 
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/download/{filename}")
async def download_file(filename: str):
    """Скачивание обработанного файла"""
    file_path = os.path.join(video_processor.output_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@router.get("/api/files")
async def list_files():
    """Получение списка обработанных файлов"""
    try:
        files = []
        for filename in os.listdir(video_processor.output_dir):
            file_path = os.path.join(video_processor.output_dir, filename)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                files.append({
                    "filename": filename,
                    "size": file_size,
                    "path": file_path
                })
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """Удаление обработанного файла"""
    file_path = os.path.join(video_processor.output_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        os.remove(file_path)
        return {"message": "File deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Мобильные endpoints
@router.get("/api/mobile/status")
async def mobile_status():
    """Статус API для мобильного клиента"""
    return {
        "status": "online",
        "version": "1.0.0",
        "features": {
            "image_processing": True,
            "video_processing": True,
            "file_download": True,
            "progress_tracking": True
        },
        "supported_formats": {
            "images": ["jpg", "jpeg", "png", "bmp"],
            "videos": ["mp4", "avi", "mov", "mkv"]
        }
    }

@router.get("/api/mobile/health")
async def mobile_health():
    """Быстрая проверка здоровья для мобильного клиента"""
    return {"status": "healthy", "timestamp": datetime.now()}

@router.post("/api/mobile/process/image")
async def mobile_process_image(file: UploadFile = File(...)):
    """Обработка изображения для мобильного клиента"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Проверяем размер файла
    await check_file_size(file)
    
    try:
        result = await video_processor.process_image(file)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/api/mobile/process/video")
async def mobile_process_video(file: UploadFile = File(...)):
    """Обработка видео для мобильного клиента"""
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Проверяем размер файла
    await check_file_size(file)
    
    try:
        # Очищаем все старые файлы перед обработкой нового
        cleaned_files = video_processor.cleanup_all_files()
        logger.info(f"Cleaned {len(cleaned_files)} old files before processing new video")
        
        # Сохраняем загруженный файл
        input_path = video_processor._get_temp_path(file.filename)
        output_path = video_processor._get_output_path(file.filename)
        
        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Импортируем функции обработки
        from ..dive_color_corrector.mobile_correct import analyze_video_mobile, process_video_mobile
        
        # Анализируем видео
        video_data = analyze_video_mobile(input_path, output_path)
        
        # Обрабатываем видео
        result = process_video_mobile(video_data)
        
        # Удаляем временный файл
        os.remove(input_path)
        
        # Добавляем информацию о файле
        result.update({
            "input_filename": file.filename,
            "output_filename": os.path.basename(output_path),
            "file_size": os.path.getsize(output_path) if os.path.exists(output_path) else 0,
            "cleaned_files_count": len(cleaned_files)
        })
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        error_message = str(e)
        if "index 0 is out of bounds" in error_message:
            error_message = "Ошибка обработки видео: не удалось проанализировать видеофайл. Проверьте корректность файла."
        elif "Не удалось получить ни одного кадра" in error_message:
            error_message = "Ошибка обработки видео: не удалось прочитать кадры из видеофайла. Проверьте формат и целостность файла."
        
        return {
            "success": False,
            "error": error_message
        }

@router.get("/api/mobile/files")
async def mobile_list_files():
    """Список файлов для мобильного клиента"""
    try:
        files = []
        for filename in os.listdir(video_processor.output_dir):
            file_path = os.path.join(video_processor.output_dir, filename)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                files.append({
                    "filename": filename,
                    "size": file_size,
                    "download_url": f"/api/download/{filename}"
                })
        
        return {
            "success": True,
            "data": {
                "files": files,
                "count": len(files)
            }
        }
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Performance management endpoints
@router.get("/api/performance/info")
async def get_performance_info_endpoint():
    """Получение информации о настройках производительности"""
    try:
        info = get_performance_info()
        return {
            "success": True,
            "data": info
        }
    except Exception as e:
        logger.error(f"Error getting performance info: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/api/performance/configure")
async def configure_performance_endpoint(
    batch_size: int = None,
    max_processes: int = None,
    video_quality: int = None,
    use_gpu: bool = None,
    enable_ffmpeg_optimization: bool = None,
    video_codec: str = None
):
    """Настройка параметров производительности"""
    try:
        configure_performance(
            batch_size=batch_size,
            max_processes=max_processes,
            video_quality=video_quality,
            use_gpu=use_gpu,
            enable_ffmpeg_optimization=enable_ffmpeg_optimization,
            video_codec=video_codec
        )
        
        return {
            "success": True,
            "message": "Performance settings updated successfully",
            "data": get_performance_info()
        }
    except Exception as e:
        logger.error(f"Error configuring performance: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

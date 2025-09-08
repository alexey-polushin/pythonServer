from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional
import logging
from datetime import datetime
import os
import io
import json

from ..models.schemas import MessageRequest, MessageResponse, HealthResponse, StatsResponse
from ..services.video_processor import video_processor

logger = logging.getLogger(__name__)

router = APIRouter()

# Хранилище сообщений (в продакшене используйте базу данных)
messages_storage = []

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
        version="1.0.0"
    )

@router.post("/api/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """Отправка сообщения и получение ответа"""
    try:
        # Генерируем простой ответ
        response_text = f"Echo: {request.message}"
        
        # Создаем ответ
        message_response = MessageResponse(
            id=f"msg_{len(messages_storage) + 1}",
            message=request.message,
            response=response_text,
            timestamp=datetime.now(),
            user_id=request.user_id
        )
        
        # Сохраняем в хранилище
        messages_storage.append(message_response)
        
        logger.info(f"Message processed: {request.message[:50]}...")
        
        return message_response
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/api/messages", response_model=List[MessageResponse])
async def get_messages(limit: int = 10):
    """Получение последних сообщений"""
    return messages_storage[-limit:] if messages_storage else []

@router.get("/api/messages/{message_id}", response_model=MessageResponse)
async def get_message(message_id: str):
    """Получение конкретного сообщения по ID"""
    for message in messages_storage:
        if message.id == message_id:
            return message
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Message not found"
    )

@router.delete("/api/messages/{message_id}")
async def delete_message(message_id: str):
    """Удаление сообщения по ID"""
    global messages_storage
    messages_storage = [msg for msg in messages_storage if msg.id != message_id]
    
    return {"message": "Message deleted successfully"}

@router.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Получение статистики сервера"""
    return StatsResponse(
        total_messages=len(messages_storage),
        server_uptime="N/A",  # В продакшене добавьте отслеживание времени работы
        timestamp=datetime.now()
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

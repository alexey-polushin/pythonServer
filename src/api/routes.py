from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
import logging
from datetime import datetime
import os

from ..models.schemas import HealthResponse
from ..services.video_processor import video_processor

logger = logging.getLogger(__name__)

router = APIRouter()


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

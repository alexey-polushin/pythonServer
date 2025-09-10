import numpy as np
import cv2
import math
import logging
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import partial

logger = logging.getLogger(__name__)

# Проверяем доступность GPU
GPU_AVAILABLE = False
GPU_TYPE = None

# Проверяем Apple Metal (MPS)
try:
    import torch
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        GPU_AVAILABLE = True
        GPU_TYPE = "MPS"
        logger.info("GPU acceleration available with Apple Metal (MPS)")
    else:
        logger.info("Apple Metal (MPS) not available")
except ImportError:
    logger.info("PyTorch not available for MPS")

# Проверяем CUDA (если MPS недоступен)
if not GPU_AVAILABLE:
    try:
        import cupy as cp
        GPU_AVAILABLE = True
        GPU_TYPE = "CUDA"
        logger.info("GPU acceleration available with CuPy (CUDA)")
    except ImportError:
        logger.info("CuPy (CUDA) not available")

if not GPU_AVAILABLE:
    logger.info("GPU acceleration not available, using CPU only")

THRESHOLD_RATIO = 2000
MIN_AVG_RED = 60
MAX_HUE_SHIFT = 120
BLUE_MAGIC_VALUE = 1.2
SAMPLE_SECONDS = 1.0  # Берем кадры каждые 1.0 секунду для ускорения анализа

# Параметры производительности
BATCH_SIZE = 4  # Минимальный размер батча для простоты
MAX_PROCESSES = 2  # Минимальное количество процессов
VIDEO_QUALITY = 100  # Максимальное качество (без сжатия)
USE_GPU = True  # Использовать GPU если доступен
ENABLE_FFMPEG_OPTIMIZATION = False  # Отключить постобработку для скорости
VIDEO_CODEC = 'mp4v'  # Кодек без потерь для сохранения качества


# Загружаем конфигурацию при импорте модуля
def _load_performance_config():
    """Загружает конфигурацию производительности"""
    global BATCH_SIZE, MAX_PROCESSES, VIDEO_QUALITY, USE_GPU, ENABLE_FFMPEG_OPTIMIZATION, VIDEO_CODEC
    
    try:
        import os
        import json
        
        config_file = os.path.join(os.path.dirname(__file__), '..', '..', 'performance_config.json')
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            BATCH_SIZE = config.get('batch_size', BATCH_SIZE)
            MAX_PROCESSES = config.get('max_processes', MAX_PROCESSES)
            VIDEO_QUALITY = config.get('video_quality', VIDEO_QUALITY)
            USE_GPU = config.get('use_gpu', USE_GPU) and GPU_AVAILABLE
            ENABLE_FFMPEG_OPTIMIZATION = config.get('enable_ffmpeg_optimization', ENABLE_FFMPEG_OPTIMIZATION)
            VIDEO_CODEC = config.get('video_codec', VIDEO_CODEC)
            
            logger.info(f"Loaded performance config: batch_size={BATCH_SIZE}, max_processes={MAX_PROCESSES}, video_quality={VIDEO_QUALITY}, use_gpu={USE_GPU}")
        else:
            # Применяем оптимальную конфигурацию для системы
            cpu_count = mp.cpu_count()
            if cpu_count >= 8:
                BATCH_SIZE = 64
                MAX_PROCESSES = 6
                VIDEO_QUALITY = 85
            elif cpu_count >= 4:
                BATCH_SIZE = 48
                MAX_PROCESSES = 3
                VIDEO_QUALITY = 80
            else:
                BATCH_SIZE = 32
                MAX_PROCESSES = 2
                VIDEO_QUALITY = 75
            
            USE_GPU = False  # По умолчанию отключаем GPU если нет конфигурации
            logger.info(f"Applied optimal config for {cpu_count} cores: batch_size={BATCH_SIZE}, max_processes={MAX_PROCESSES}")
            
    except Exception as e:
        logger.warning(f"Error loading performance config: {e}, using defaults")

# Загружаем конфигурацию при импорте
_load_performance_config()

def _save_performance_config():
    """Сохраняет текущую конфигурацию производительности в файл"""
    try:
        import os
        import json
        
        config_file = os.path.join(os.path.dirname(__file__), '..', '..', 'performance_config.json')
        
        config = {
            "batch_size": BATCH_SIZE,
            "max_processes": MAX_PROCESSES,
            "video_quality": VIDEO_QUALITY,
            "use_gpu": USE_GPU,
            "auto_configure": False
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Performance config saved to: {config_file}")
        
    except Exception as e:
        logger.error(f"Error saving performance config: {e}")

def configure_performance(batch_size=None, max_processes=None, video_quality=None, use_gpu=None, enable_ffmpeg_optimization=None, video_codec=None):
    """Настраивает параметры производительности"""
    global BATCH_SIZE, MAX_PROCESSES, VIDEO_QUALITY, USE_GPU, ENABLE_FFMPEG_OPTIMIZATION, VIDEO_CODEC
    
    config_changed = False
    
    if batch_size is not None:
        BATCH_SIZE = max(1, min(batch_size, 128))  # Ограничиваем от 1 до 128
        logger.info(f"Batch size set to: {BATCH_SIZE}")
        config_changed = True
    
    if max_processes is not None:
        MAX_PROCESSES = max(1, min(max_processes, mp.cpu_count()))
        logger.info(f"Max processes set to: {MAX_PROCESSES}")
        config_changed = True
    
    if video_quality is not None:
        VIDEO_QUALITY = max(1, min(video_quality, 100))  # Ограничиваем от 1 до 100
        logger.info(f"Video quality set to: {VIDEO_QUALITY}%")
        config_changed = True
    
    if use_gpu is not None:
        USE_GPU = use_gpu and GPU_AVAILABLE
        logger.info(f"GPU usage set to: {USE_GPU}")
        config_changed = True
    
    if enable_ffmpeg_optimization is not None:
        ENABLE_FFMPEG_OPTIMIZATION = enable_ffmpeg_optimization
        logger.info(f"FFmpeg optimization set to: {ENABLE_FFMPEG_OPTIMIZATION}")
        config_changed = True
    
    if video_codec is not None:
        valid_codecs = ['mp4v']  # Только mp4v - оптимальный по весу и скорости
        if video_codec in valid_codecs:
            VIDEO_CODEC = video_codec
            logger.info(f"Video codec set to: {VIDEO_CODEC}")
            config_changed = True
        else:
            logger.warning(f"Invalid codec: {video_codec}. Valid options: {valid_codecs}")
    
    # Сохраняем конфигурацию в файл если что-то изменилось
    if config_changed:
        _save_performance_config()

def get_performance_info():
    """Возвращает информацию о текущих настройках производительности"""
    return {
        "batch_size": BATCH_SIZE,
        "max_processes": MAX_PROCESSES,
        "video_quality": VIDEO_QUALITY,
        "use_gpu": USE_GPU,
        "gpu_available": GPU_AVAILABLE,
        "gpu_type": GPU_TYPE,
        "cpu_count": mp.cpu_count(),
        "enable_ffmpeg_optimization": ENABLE_FFMPEG_OPTIMIZATION,
        "video_codec": VIDEO_CODEC
    }

def get_video_bitrate(video_path):
    """Получает битрейт видео и аудио из метаданных"""
    try:
        import subprocess
        import json
        
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_streams', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            video_bitrate = None
            audio_bitrate = None
            
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video' and 'bit_rate' in stream:
                    video_bitrate = int(stream['bit_rate'])
                elif stream.get('codec_type') == 'audio' and 'bit_rate' in stream:
                    audio_bitrate = int(stream['bit_rate'])
            
            logger.info(f"Video bitrate: {video_bitrate}, Audio bitrate: {audio_bitrate}")
            return video_bitrate, audio_bitrate
        else:
            logger.warning(f"Failed to get bitrate info: {result.stderr}")
            return None, None
            
    except Exception as e:
        logger.warning(f"Error getting video bitrate: {e}")
        return None, None

def get_video_rotation(video_path):
    """Определяет угол поворота видео из метаданных"""
    logger.info(f"Analyzing video rotation for: {video_path}")
    
    try:
        # Сначала пробуем ffprobe для получения метаданных
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_streams', '-select_streams', 'v:0', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            logger.info(f"ffprobe raw output: {result.stdout[:500]}...")  # Первые 500 символов
            
            if 'streams' in data and len(data['streams']) > 0:
                stream = data['streams'][0]
                logger.info(f"Stream data keys: {list(stream.keys())}")
                
                # Проверяем различные поля для определения поворота
                rotation = 0
                if 'tags' in stream:
                    logger.info(f"Stream tags: {stream['tags']}")
                    if 'rotate' in stream['tags']:
                        rotation = int(stream['tags']['rotate'])
                        logger.info(f"Found rotation in tags: {rotation} degrees")
                
                if 'side_data_list' in stream:
                    logger.info(f"Side data list: {stream['side_data_list']}")
                    for side_data in stream['side_data_list']:
                        if side_data.get('side_data_type') == 'Display Matrix':
                            matrix = side_data.get('displaymatrix', '')
                            logger.info(f"Display matrix: {matrix}")
                            if '90' in matrix:
                                rotation = 90
                            elif '180' in matrix:
                                rotation = 180
                            elif '270' in matrix:
                                rotation = 270
                
                # Получаем размеры видео
                width = stream.get('width', 0)
                height = stream.get('height', 0)
                logger.info(f"Video dimensions from ffprobe: {width}x{height}")
                
            logger.info(f"Final detected rotation via ffprobe: {rotation} degrees")
            
            # НЕ применяем автоматический поворот для портретных видео
            # Поворот должен определяться только из метаданных видео
            if rotation == 0 and height > width:
                logger.info("ffprobe shows 0° and video appears to be PORTRAIT")
                logger.info("No rotation metadata found - keeping original orientation")
                return 0
            
            return rotation
    except Exception as e:
        logger.warning(f"Could not detect video rotation via ffprobe: {str(e)}")
    
    # Альтернативный способ через OpenCV (если ffprobe недоступен)
    try:
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            cap.release()
            
            logger.info(f"Video dimensions from OpenCV: {width}x{height}")
            logger.info(f"Video aspect ratio: {height/width if width > 0 else 'unknown'}")
            
            if height > width:
                logger.info("Video appears to be in PORTRAIT orientation")
                logger.info("No rotation metadata found - keeping original orientation")
            else:
                logger.info("Video appears to be in LANDSCAPE orientation")
            
            return 0
    except Exception as e:
        logger.warning(f"Could not analyze video with OpenCV: {str(e)}")
    
    return 0

def apply_rotation(frame, rotation_angle):
    """Применяет поворот к кадру"""
    if rotation_angle == 0:
        return frame
    
    if rotation_angle == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rotation_angle == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    elif rotation_angle == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    
    return frame

def get_rotated_dimensions(width, height, rotation_angle):
    """Возвращает размеры после поворота"""
    if rotation_angle in [90, 270]:
        return height, width
    return width, height


def hue_shift_red(mat, h):
    """Сдвиг оттенка красного канала"""
    U = math.cos(h * math.pi / 180)
    W = math.sin(h * math.pi / 180)

    r = (0.299 + 0.701 * U + 0.168 * W) * mat[..., 0]
    g = (0.587 - 0.587 * U + 0.330 * W) * mat[..., 1]
    b = (0.114 - 0.114 * U - 0.497 * W) * mat[..., 2]

    return np.dstack([r, g, b])

def normalizing_interval(array):
    """Находит интервал нормализации"""
    high = 255
    low = 0
    max_dist = 0

    for i in range(1, len(array)):
        dist = array[i] - array[i-1]
        if(dist > max_dist):
            max_dist = dist
            high = array[i]
            low = array[i-1]

    return (low, high)

def apply_filter_gpu(mat, filt):
    """Применяет фильтр к изображению с GPU ускорением"""
    if not GPU_AVAILABLE:
        return apply_filter_cpu(mat, filt)
    
    try:
        if GPU_TYPE == "MPS":
            return apply_filter_mps(mat, filt)
        elif GPU_TYPE == "CUDA":
            return apply_filter_cuda(mat, filt)
        else:
            return apply_filter_cpu(mat, filt)
    except Exception as e:
        logger.warning(f"GPU processing failed, falling back to CPU: {str(e)}")
        return apply_filter_cpu(mat, filt)

def apply_filter_mps(mat, filt):
    """Применяет фильтр с Apple Metal (MPS) ускорением"""
    import torch
    
    # Переносим данные на GPU
    device = torch.device("mps")
    mat_tensor = torch.from_numpy(mat.astype(np.float32)).to(device)
    filt_tensor = torch.from_numpy(np.array(filt, dtype=np.float32)).to(device)
    
    # Применяем фильтр на GPU
    filtered_mat = mat_tensor.clone()
    
    # Красный канал
    filtered_mat[..., 0] = (mat_tensor[..., 0] * filt_tensor[0] + 
                           mat_tensor[..., 1] * filt_tensor[1] + 
                           mat_tensor[..., 2] * filt_tensor[2] + 
                           filt_tensor[4] * 255)
    
    # Зеленый канал
    filtered_mat[..., 1] = (mat_tensor[..., 1] * filt_tensor[6] + 
                           filt_tensor[9] * 255)
    
    # Синий канал
    filtered_mat[..., 2] = (mat_tensor[..., 2] * filt_tensor[12] + 
                           filt_tensor[14] * 255)

    # Обрезаем значения и конвертируем обратно в uint8
    filtered_mat = torch.clamp(filtered_mat, 0, 255)
    result = filtered_mat.cpu().numpy().astype(np.uint8)
    
    return result

def apply_filter_cuda(mat, filt):
    """Применяет фильтр с CUDA ускорением"""
    import cupy as cp
    
    # Переносим данные на GPU
    mat_gpu = cp.asarray(mat, dtype=cp.float32)
    filt_gpu = cp.asarray(filt, dtype=cp.float32)
    
    # Применяем фильтр на GPU
    filtered_mat_gpu = mat_gpu.copy()
    
    filtered_mat_gpu[..., 0] = (mat_gpu[..., 0] * filt_gpu[0] + 
                               mat_gpu[..., 1] * filt_gpu[1] + 
                               mat_gpu[..., 2] * filt_gpu[2] + 
                               filt_gpu[4] * 255)
    
    filtered_mat_gpu[..., 1] = (mat_gpu[..., 1] * filt_gpu[6] + 
                               filt_gpu[9] * 255)
    
    filtered_mat_gpu[..., 2] = (mat_gpu[..., 2] * filt_gpu[12] + 
                               filt_gpu[14] * 255)

    # Обрезаем значения и конвертируем обратно в uint8
    cp.clip(filtered_mat_gpu, 0, 255, out=filtered_mat_gpu)
    result = cp.asnumpy(filtered_mat_gpu.astype(cp.uint8))
    
    return result

def apply_filter_cpu(mat, filt):
    """Применяет фильтр к изображению на CPU (оригинальная версия)"""
    # Используем in-place операции для экономии памяти
    filtered_mat = mat.astype(np.float32)
    
    # Применяем фильтр напрямую к массиву
    filtered_mat[..., 0] = (mat[..., 0] * filt[0] + 
                           mat[..., 1] * filt[1] + 
                           mat[..., 2] * filt[2] + 
                           filt[4] * 255)
    
    filtered_mat[..., 1] = (mat[..., 1] * filt[6] + 
                           filt[9] * 255)
    
    filtered_mat[..., 2] = (mat[..., 2] * filt[12] + 
                           filt[14] * 255)

    # Обрезаем значения и конвертируем обратно в uint8
    np.clip(filtered_mat, 0, 255, out=filtered_mat)
    return filtered_mat.astype(np.uint8)

def apply_filter(mat, filt):
    """Применяет фильтр к изображению (автоматически выбирает GPU или CPU)"""
    if USE_GPU and GPU_AVAILABLE:
        return apply_filter_gpu(mat, filt)
    else:
        return apply_filter_cpu(mat, filt)


def get_filter_matrix(mat):
    """Получает матрицу фильтра для коррекции цветов (оптимизированная версия)"""
    # Используем более эффективное изменение размера
    if mat.shape[:2] != (256, 256):
        mat = cv2.resize(mat, (256, 256), interpolation=cv2.INTER_LINEAR)

    # Получаем средние значения RGB более эффективно
    avg_mat = np.mean(mat.reshape(-1, 3), axis=0).astype(np.uint8)
    
    # Оптимизированный поиск сдвига оттенка
    new_avg_r = avg_mat[0]
    hue_shift = 0
    
    # Предвычисляем константы для оптимизации
    cos_h = math.cos(hue_shift * math.pi / 180)
    sin_h = math.sin(hue_shift * math.pi / 180)
    
    while new_avg_r < MIN_AVG_RED and hue_shift <= MAX_HUE_SHIFT:
        # Оптимизированное вычисление сдвига оттенка
        shifted_r = (0.299 + 0.701 * cos_h + 0.168 * sin_h) * avg_mat[0]
        shifted_g = (0.587 - 0.587 * cos_h + 0.330 * sin_h) * avg_mat[1]
        shifted_b = (0.114 - 0.114 * cos_h - 0.497 * sin_h) * avg_mat[2]
        new_avg_r = shifted_r + shifted_g + shifted_b
        
        hue_shift += 1
        if hue_shift <= MAX_HUE_SHIFT:
            cos_h = math.cos(hue_shift * math.pi / 180)
            sin_h = math.sin(hue_shift * math.pi / 180)

    # Применяем сдвиг оттенка ко всему изображению
    shifted_mat = hue_shift_red(mat, hue_shift)
    new_r_channel = np.sum(shifted_mat, axis=2)
    new_r_channel = np.clip(new_r_channel, 0, 255)
    mat[..., 0] = new_r_channel

    # Оптимизированное вычисление гистограмм
    hist_r = cv2.calcHist([mat], [0], None, [256], [0, 256])
    hist_g = cv2.calcHist([mat], [1], None, [256], [0, 256])
    hist_b = cv2.calcHist([mat], [2], None, [256], [0, 256])

    # Векторизованная обработка нормализации
    threshold_level = (mat.shape[0] * mat.shape[1]) / THRESHOLD_RATIO
    normalize_mat = np.zeros((256, 3))
    
    # Используем векторизованные операции вместо циклов
    r_mask = hist_r.flatten() < threshold_level
    g_mask = hist_g.flatten() < threshold_level
    b_mask = hist_b.flatten() < threshold_level
    
    normalize_mat[r_mask, 0] = np.arange(256)[r_mask]
    normalize_mat[g_mask, 1] = np.arange(256)[g_mask]
    normalize_mat[b_mask, 2] = np.arange(256)[b_mask]

    normalize_mat[255] = 255

    adjust_r_low, adjust_r_high = normalizing_interval(normalize_mat[..., 0])
    adjust_g_low, adjust_g_high = normalizing_interval(normalize_mat[..., 1])
    adjust_b_low, adjust_b_high = normalizing_interval(normalize_mat[..., 2])

    # Предвычисляем сдвиг для финального hue_shift
    final_cos_h = math.cos(hue_shift * math.pi / 180)
    final_sin_h = math.sin(hue_shift * math.pi / 180)
    
    shifted_r = 0.299 + 0.701 * final_cos_h + 0.168 * final_sin_h
    shifted_g = 0.587 - 0.587 * final_cos_h + 0.330 * final_sin_h
    shifted_b = 0.114 - 0.114 * final_cos_h - 0.497 * final_sin_h

    # Предотвращаем деление на ноль
    r_range = max(adjust_r_high - adjust_r_low, 1)
    g_range = max(adjust_g_high - adjust_g_low, 1)
    b_range = max(adjust_b_high - adjust_b_low, 1)
    
    red_gain = 256 / r_range
    green_gain = 256 / g_range
    blue_gain = 256 / b_range

    redOffset = (-adjust_r_low / 256) * red_gain
    greenOffset = (-adjust_g_low / 256) * green_gain
    blueOffset = (-adjust_b_low / 256) * blue_gain

    adjust_red = shifted_r * red_gain
    adjust_red_green = shifted_g * red_gain
    adjust_red_blue = shifted_b * red_gain * BLUE_MAGIC_VALUE

    return np.array([
        adjust_red, adjust_red_green, adjust_red_blue, 0, redOffset,
        0, green_gain, 0, 0, greenOffset,
        0, 0, blue_gain, 0, blueOffset,
        0, 0, 0, 1, 0,
    ])

def correct_image_mobile(input_path, output_path):
    """Обрабатывает изображение без GUI зависимостей"""
    try:
        mat = cv2.imread(input_path)
        if mat is None:
            raise ValueError(f"Не удалось загрузить изображение: {input_path}")
        
        # Определяем поворот изображения (для изображений обычно 0, но может быть полезно)
        rotation_angle = 0  # Для изображений поворот обычно не применяется
            
        # Применяем поворот если необходимо
        rotated_mat = apply_rotation(mat, rotation_angle)
            
        rgb_mat = cv2.cvtColor(rotated_mat, cv2.COLOR_BGR2RGB)
        filter_matrix = get_filter_matrix(rgb_mat)
        corrected_mat = apply_filter(rgb_mat, filter_matrix)
        corrected_mat = cv2.cvtColor(corrected_mat, cv2.COLOR_RGB2BGR)

        success = cv2.imwrite(output_path, corrected_mat)
        if not success:
            raise ValueError(f"Не удалось сохранить изображение: {output_path}")
            
        return {
            "status": "success",
            "input_path": input_path,
            "output_path": output_path,
            "message": "Image processed successfully",
            "rotation_applied": rotation_angle
        }
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return {
            "status": "error",
            "message": f"Error processing image: {str(e)}"
        }

def _process_frame_for_analysis(args):
    """Обрабатывает один кадр для анализа (для многопроцессной обработки)"""
    frame_data, frame_number, rotation_angle = args
    try:
        # Декодируем кадр из байтов
        frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            return None
            
        # Применяем поворот к кадру перед анализом
        rotated_frame = apply_rotation(frame, rotation_angle)
        mat = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2RGB)
        filter_matrix = get_filter_matrix(mat)
        
        return frame_number, filter_matrix
    except Exception as e:
        logger.warning(f"Ошибка при обработке кадра {frame_number}: {str(e)}")
        return None

def analyze_video_mobile(input_video_path, output_video_path, progress_callback=None):
    """Анализирует видео для мобильного API (оптимизированная версия)"""
    try:
        # Определяем поворот видео и битрейт
        rotation_angle = get_video_rotation(input_video_path)
        video_bitrate, audio_bitrate = get_video_bitrate(input_video_path)
        
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Не удалось открыть видео: {input_video_path}")
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        # Более точное определение количества кадров через ffprobe
        try:
            import subprocess
            cmd = ['ffprobe', '-v', 'quiet', '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames', '-of', 'csv=p=0', input_video_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                frame_count = int(result.stdout.strip())
                logger.info(f"Frame count from ffprobe: {frame_count}")
            else:
                frame_count = math.ceil(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                logger.warning(f"Using OpenCV frame count: {frame_count}")
        except Exception as e:
            frame_count = math.ceil(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            logger.warning(f"Error getting frame count from ffprobe: {e}, using OpenCV: {frame_count}")
        
        logger.info(f"Video info: FPS={fps}, Frame count={frame_count}")
        
        # Собираем кадры для анализа
        frames_to_analyze = []
        count = 0
        
        logger.info("Starting video analysis...")
        
        while(cap.isOpened()):
            ret, frame = cap.read()
            if not ret:
                if count >= frame_count:
                    logger.info(f"Reached expected frame count in analysis: {frame_count}")
                    break
                if count >= 1e6:  # Защита от бесконечного цикла
                    logger.warning(f"Reached maximum frame limit in analysis: {count}")
                    break
                logger.warning(f"Failed to read frame {count + 1} in analysis, continuing...")
                continue
            
            count += 1

            # Выбираем кадры для анализа каждые N секунд
            if count % int(fps * SAMPLE_SECONDS) == 0:
                # Кодируем кадр в байты для передачи в процессы
                _, encoded_frame = cv2.imencode('.jpg', frame)
                frames_to_analyze.append((encoded_frame.tobytes(), count, rotation_angle))
                
                if progress_callback:
                    progress_callback({
                        "stage": "analyzing",
                        "progress": (count / frame_count) * 30,  # Сбор кадров занимает 30% времени
                        "frames_processed": count,
                        "total_frames": frame_count
                    })
        
        cap.release()

        # Проверяем, что мы получили хотя бы один кадр для анализа
        if not frames_to_analyze:
            raise ValueError("Не удалось получить ни одного кадра для анализа. Проверьте корректность видеофайла.")
        
        # Многопроцессная обработка кадров
        logger.info(f"Processing {len(frames_to_analyze)} frames with multiprocessing...")
        
        # Определяем количество процессов (не больше количества кадров)
        num_processes = min(mp.cpu_count(), len(frames_to_analyze))
        
        filter_matrix_indexes = []
        filter_matrices = []
        
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            results = list(executor.map(_process_frame_for_analysis, frames_to_analyze))
            
            # Собираем результаты
            for result in results:
                if result is not None:
                    frame_number, filter_matrix = result
                    filter_matrix_indexes.append(frame_number)
                    filter_matrices.append(filter_matrix)
        
        # Сортируем результаты по номеру кадра
        sorted_data = sorted(zip(filter_matrix_indexes, filter_matrices))
        filter_matrix_indexes, filter_matrices = zip(*sorted_data) if sorted_data else ([], [])
        
        if progress_callback:
            progress_callback({
                "stage": "analyzing",
                "progress": 50,  # Анализ завершен
                "frames_processed": count,
                "total_frames": frame_count
            })
        
        filter_matrices = np.array(filter_matrices) if filter_matrices else np.array([])
        
        return {
            "input_video_path": input_video_path,
            "output_video_path": output_video_path,
            "fps": fps,
            "frame_count": count,
            "filters": filter_matrices,
            "filter_indices": list(filter_matrix_indexes),
            "rotation_angle": rotation_angle,
            "original_bitrate": video_bitrate,
            "original_audio_bitrate": audio_bitrate
        }
        
    except Exception as e:
        logger.error(f"Error analyzing video: {str(e)}")
        raise


def _process_frame_batch(args):
    """Обрабатывает батч кадров (для многопроцессной обработки) - оптимизированная версия"""
    frames_data, frame_numbers, filter_matrices, filter_indices, rotation_angle = args
    try:
        processed_frames = []
        
        for i, (frame_data, frame_number) in enumerate(zip(frames_data, frame_numbers)):
            # Декодируем кадр из байтов
            frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                continue
                
            # Применяем поворот к кадру
            rotated_frame = apply_rotation(frame, rotation_angle)
            
            # Применяем фильтр
            rgb_mat = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2RGB)
            
            # Интерполируем матрицу фильтра
            if len(filter_matrices) > 0:
                interpolated_filter = [np.interp(frame_number, filter_indices, filter_matrices[..., x]) 
                                     for x in range(len(filter_matrices[0]))]
                corrected_mat = apply_filter(rgb_mat, interpolated_filter)
                corrected_mat = cv2.cvtColor(corrected_mat, cv2.COLOR_RGB2BGR)
            else:
                corrected_mat = rotated_frame
            
            # Кодируем обработанный кадр обратно в байты
            _, encoded_frame = cv2.imencode('.jpg', corrected_mat)
            processed_frames.append((frame_number, encoded_frame.tobytes()))
        
        return processed_frames
    except Exception as e:
        logger.warning(f"Ошибка при обработке батча кадров: {str(e)}")
        return []

def process_video_mobile(video_data, progress_callback=None):
    """Обрабатывает видео для мобильного API (оптимизированная версия)"""
    try:
        cap = cv2.VideoCapture(video_data["input_video_path"])
        if not cap.isOpened():
            raise ValueError(f"Не удалось открыть видео: {video_data['input_video_path']}")

        # Оптимизируем настройки чтения видео
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Уменьшаем буфер для экономии памяти
        
        frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        # Получаем угол поворота из данных анализа
        rotation_angle = video_data.get("rotation_angle", 0)
        logger.info(f"Processing video with rotation angle: {rotation_angle} degrees")
        logger.info(f"Original video dimensions: {frame_width}x{frame_height}")
        
        # Определяем размеры после поворота
        output_width, output_height = get_rotated_dimensions(frame_width, frame_height, rotation_angle)
        logger.info(f"Output video dimensions after rotation: {output_width}x{output_height}")

        # Используем настроенный кодек
        fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
        logger.info(f"Using video codec: {VIDEO_CODEC}")
        new_video = cv2.VideoWriter(
            video_data["output_video_path"], 
            fourcc, 
            video_data["fps"], 
            (int(output_width), int(output_height))
        )
        
        # Настраиваем параметры кодека для сохранения качества (без сжатия)
        if hasattr(new_video, 'set'):
            # Устанавливаем максимальное качество для сохранения оригинального качества
            new_video.set(cv2.VIDEOWRITER_PROP_QUALITY, 100)  # Максимальное качество
            logger.info(f"Set video quality to: 100% (no compression) with {VIDEO_CODEC} codec")

        filter_matrices = video_data["filters"]
        filter_indices = video_data["filter_indices"]

        logger.info("Starting video processing...")

        frame_count = video_data["frame_count"]
        count = 0
        
        # Параметры для батчевой обработки
        batch_size = BATCH_SIZE
        frames_batch = []
        frame_numbers_batch = []
        
        # Создаем новый VideoCapture для обработки (позиция сброшена)
        cap = cv2.VideoCapture(video_data["input_video_path"])
        
        # Определяем количество процессов для обработки
        num_processes = min(mp.cpu_count(), MAX_PROCESSES)
        
        # Простая последовательная обработка (как в оригинале)
        while(cap.isOpened()):
            ret, frame = cap.read()
            
            if not ret:
                if count >= frame_count:
                    logger.info(f"Reached expected frame count: {frame_count}")
                    break
                if count >= 1e6:  # Защита от бесконечного цикла
                    logger.warning(f"Reached maximum frame limit: {count}")
                    break
                logger.warning(f"Failed to read frame {count + 1}, continuing...")
                continue
            
            count += 1

            # Кодируем кадр в JPG для скорости
            _, encoded_frame = cv2.imencode('.jpg', frame)
            frames_batch.append(encoded_frame.tobytes())
            frame_numbers_batch.append(count)
            
            # Обрабатываем батч когда он заполнен
            if len(frames_batch) >= batch_size:
                if frames_batch:
                    # Многопроцессная обработка батча
                    batch_args = (frames_batch, frame_numbers_batch, filter_matrices, 
                                filter_indices, rotation_angle)
                    
                    # Создаем локальный пул процессов для каждого батча
                    with ProcessPoolExecutor(max_workers=num_processes) as executor:
                        results = list(executor.map(_process_frame_batch, [batch_args]))
                    
                    # Записываем обработанные кадры в видео
                    for result in results:
                        for frame_number, processed_frame_data in result:
                            processed_frame = cv2.imdecode(
                                np.frombuffer(processed_frame_data, dtype=np.uint8), 
                                cv2.IMREAD_COLOR
                            )
                            if processed_frame is not None:
                                new_video.write(processed_frame)
                    
                    # Очищаем батч
                    frames_batch = []
                    frame_numbers_batch = []
        
        # Обрабатываем оставшиеся кадры
        if frames_batch:
            logger.info(f"Processing remaining {len(frames_batch)} frames...")
            batch_args = (frames_batch, frame_numbers_batch, filter_matrices, 
                        filter_indices, rotation_angle)
            
            # Создаем локальный пул процессов для оставшихся кадров
            with ProcessPoolExecutor(max_workers=num_processes) as executor:
                results = list(executor.map(_process_frame_batch, [batch_args]))
            
            # Записываем обработанные кадры в видео
            for result in results:
                for frame_number, processed_frame_data in result:
                    processed_frame = cv2.imdecode(
                        np.frombuffer(processed_frame_data, dtype=np.uint8), 
                        cv2.IMREAD_COLOR
                    )
                    if processed_frame is not None:
                        new_video.write(processed_frame)

        cap.release()
        new_video.release()
        
        logger.info(f"Video processing completed. Processed {count} frames out of {frame_count} expected.")
        
        # Оптимизируем видео через ffmpeg для лучшего сжатия (если включено)
        if ENABLE_FFMPEG_OPTIMIZATION:
            optimized_path = video_data["output_video_path"].replace('.mp4', '_optimized.mp4')
            try:
                import subprocess
                import os
                # Используем ffmpeg для оптимизации сжатия с битрейтом оригинального видео
                original_bitrate = video_data.get("original_bitrate", 2800000)  # 2.8 Mbps по умолчанию
                original_audio_bitrate = video_data.get("original_audio_bitrate", 75000)  # 75 kbps по умолчанию
                
                cmd = [
                    'ffmpeg', '-y', '-i', video_data["output_video_path"],
                    '-c:v', 'libx264', '-preset', 'ultrafast', 
                    '-b:v', f'{original_bitrate}',  # Используем битрейт оригинального видео
                    '-maxrate', f'{original_bitrate}', '-bufsize', f'{original_bitrate * 2}',
                    '-c:a', 'aac', '-b:a', f'{original_audio_bitrate}',
                    '-movflags', '+faststart',
                    '-threads', '2',  # Используем 2 потока для ускорения
                    optimized_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0 and os.path.exists(optimized_path):
                    # Заменяем оригинальный файл оптимизированным
                    os.replace(optimized_path, video_data["output_video_path"])
                    logger.info("Video optimized with ffmpeg for better compression")
                else:
                    logger.warning(f"FFmpeg optimization failed: {result.stderr}")
            except Exception as e:
                logger.warning(f"Could not optimize video with ffmpeg: {e}")
        else:
            logger.info("FFmpeg optimization disabled - using original file")
        
        return {
            "status": "success",
            "output_path": video_data["output_video_path"],
            "message": "Video processed successfully",
            "rotation_applied": rotation_angle,
            "original_dimensions": (int(frame_width), int(frame_height)),
            "output_dimensions": (int(output_width), int(output_height))
        }
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise

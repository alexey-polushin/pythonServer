import numpy as np
import cv2
import math
import logging
import subprocess
import json

logger = logging.getLogger(__name__)

THRESHOLD_RATIO = 2000
MIN_AVG_RED = 60
MAX_HUE_SHIFT = 120
BLUE_MAGIC_VALUE = 1.2
SAMPLE_SECONDS = 2

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
            
            # Проверяем портретную ориентацию даже если ffprobe показывает 0°
            if rotation == 0 and height > width:
                logger.info("ffprobe shows 0° but video appears to be PORTRAIT - applying auto-correction")
                logger.info("Auto-correcting portrait video with 90-degree rotation")
                return 90
            
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
                logger.info("Auto-correcting portrait video with 90-degree rotation")
                return 90
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

def apply_filter(mat, filt):
    """Применяет фильтр к изображению"""
    r = mat[..., 0]
    g = mat[..., 1]
    b = mat[..., 2]

    r = r * filt[0] + g*filt[1] + b*filt[2] + filt[4]*255
    g = g * filt[6] + filt[9] * 255
    b = b * filt[12] + filt[14] * 255

    filtered_mat = np.dstack([r, g, b])
    filtered_mat = np.clip(filtered_mat, 0, 255).astype(np.uint8)

    return filtered_mat

def get_filter_matrix(mat):
    """Получает матрицу фильтра для коррекции цветов"""
    mat = cv2.resize(mat, (256, 256))

    # Получаем средние значения RGB
    avg_mat = np.array(cv2.mean(mat)[:3], dtype=np.uint8)
    
    # Находим сдвиг оттенка для достижения MIN_AVG_RED
    new_avg_r = avg_mat[0]
    hue_shift = 0
    while(new_avg_r < MIN_AVG_RED):
        shifted = hue_shift_red(avg_mat, hue_shift)
        new_avg_r = np.sum(shifted)
        hue_shift += 1
        if hue_shift > MAX_HUE_SHIFT:
            new_avg_r = MIN_AVG_RED

    # Применяем сдвиг оттенка ко всему изображению
    shifted_mat = hue_shift_red(mat, hue_shift)
    new_r_channel = np.sum(shifted_mat, axis=2)
    new_r_channel = np.clip(new_r_channel, 0, 255)
    mat[..., 0] = new_r_channel

    # Получаем гистограммы всех каналов
    hist_r = cv2.calcHist([mat], [0], None, [256], [0,256])
    hist_g = cv2.calcHist([mat], [1], None, [256], [0,256])
    hist_b = cv2.calcHist([mat], [2], None, [256], [0,256])

    normalize_mat = np.zeros((256, 3))
    threshold_level = (mat.shape[0]*mat.shape[1])/THRESHOLD_RATIO
    for x in range(256):
        if hist_r[x] < threshold_level:
            normalize_mat[x][0] = x
        if hist_g[x] < threshold_level:
            normalize_mat[x][1] = x
        if hist_b[x] < threshold_level:
            normalize_mat[x][2] = x

    normalize_mat[255][0] = 255
    normalize_mat[255][1] = 255
    normalize_mat[255][2] = 255

    adjust_r_low, adjust_r_high = normalizing_interval(normalize_mat[..., 0])
    adjust_g_low, adjust_g_high = normalizing_interval(normalize_mat[..., 1])
    adjust_b_low, adjust_b_high = normalizing_interval(normalize_mat[..., 2])

    shifted = hue_shift_red(np.array([1, 1, 1]), hue_shift)
    shifted_r, shifted_g, shifted_b = shifted[0][0]

    red_gain = 256 / (adjust_r_high - adjust_r_low)
    green_gain = 256 / (adjust_g_high - adjust_g_low)
    blue_gain = 256 / (adjust_b_high - adjust_b_low)

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

def analyze_video_mobile(input_video_path, output_video_path, progress_callback=None):
    """Анализирует видео для мобильного API"""
    try:
        # Определяем поворот видео
        rotation_angle = get_video_rotation(input_video_path)
        
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Не удалось открыть видео: {input_video_path}")
            
        fps = math.ceil(cap.get(cv2.CAP_PROP_FPS))
        frame_count = math.ceil(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        filter_matrix_indexes = []
        filter_matrices = []
        count = 0
        
        logger.info("Starting video analysis...")
        
        while(cap.isOpened()):
            count += 1
            ret, frame = cap.read()
            if not ret:
                if count >= frame_count:
                    break
                if count >= 1e6:
                    break
                continue

            # Выбираем матрицу фильтра каждые N секунд
            if count % (fps * SAMPLE_SECONDS) == 0:
                try:
                    # Применяем поворот к кадру перед анализом
                    rotated_frame = apply_rotation(frame, rotation_angle)
                    mat = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2RGB)
                    filter_matrix_indexes.append(count) 
                    filter_matrices.append(get_filter_matrix(mat))
                except Exception as e:
                    logger.warning(f"Ошибка при обработке кадра {count}: {str(e)}")
                    continue
                
                if progress_callback:
                    progress_callback({
                        "stage": "analyzing",
                        "progress": (count / frame_count) * 50,  # Анализ занимает 50% времени
                        "frames_processed": count,
                        "total_frames": frame_count
                    })
        
        cap.release()

        # Проверяем, что мы получили хотя бы одну матрицу фильтра
        if not filter_matrices:
            raise ValueError("Не удалось получить ни одного кадра для анализа. Проверьте корректность видеофайла.")
        
        filter_matrices = np.array(filter_matrices)
        
        return {
            "input_video_path": input_video_path,
            "output_video_path": output_video_path,
            "fps": fps,
            "frame_count": count,
            "filters": filter_matrices,
            "filter_indices": filter_matrix_indexes,
            "rotation_angle": rotation_angle
        }
        
    except Exception as e:
        logger.error(f"Error analyzing video: {str(e)}")
        raise

def process_video_mobile(video_data, progress_callback=None):
    """Обрабатывает видео для мобильного API"""
    try:
        cap = cv2.VideoCapture(video_data["input_video_path"])
        if not cap.isOpened():
            raise ValueError(f"Не удалось открыть видео: {video_data['input_video_path']}")

        frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        # Получаем угол поворота из данных анализа
        rotation_angle = video_data.get("rotation_angle", 0)
        logger.info(f"Processing video with rotation angle: {rotation_angle} degrees")
        logger.info(f"Original video dimensions: {frame_width}x{frame_height}")
        
        # Определяем размеры после поворота
        output_width, output_height = get_rotated_dimensions(frame_width, frame_height, rotation_angle)
        logger.info(f"Output video dimensions after rotation: {output_width}x{output_height}")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        new_video = cv2.VideoWriter(
            video_data["output_video_path"], 
            fourcc, 
            video_data["fps"], 
            (int(output_width), int(output_height))
        )

        filter_matrices = video_data["filters"]
        filter_indices = video_data["filter_indices"]

        def get_interpolated_filter_matrix(frame_number):
            if len(filter_matrices) == 0:
                raise ValueError("Нет доступных матриц фильтра для интерполяции")
            return [np.interp(frame_number, filter_indices, filter_matrices[..., x]) for x in range(len(filter_matrices[0]))]

        logger.info("Starting video processing...")

        frame_count = video_data["frame_count"]
        count = 0
        
        cap = cv2.VideoCapture(video_data["input_video_path"])
        while(cap.isOpened()):
            count += 1
            ret, frame = cap.read()
            
            if not ret:
                if count >= frame_count:
                    break
                if count >= 1e6:
                    break
                continue

            # Применяем поворот к кадру
            rotated_frame = apply_rotation(frame, rotation_angle)
            
            # Применяем фильтр
            rgb_mat = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2RGB)
            interpolated_filter_matrix = get_interpolated_filter_matrix(count)
            corrected_mat = apply_filter(rgb_mat, interpolated_filter_matrix)
            corrected_mat = cv2.cvtColor(corrected_mat, cv2.COLOR_RGB2BGR)

            new_video.write(corrected_mat)
            
            if progress_callback:
                progress = 50 + (count / frame_count) * 50  # Обработка занимает оставшиеся 50%
                progress_callback({
                    "stage": "processing",
                    "progress": progress,
                    "frames_processed": count,
                    "total_frames": frame_count
                })

        cap.release()
        new_video.release()
        
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

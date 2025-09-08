import numpy as np
import cv2
import math
import logging

logger = logging.getLogger(__name__)

THRESHOLD_RATIO = 2000
MIN_AVG_RED = 60
MAX_HUE_SHIFT = 120
BLUE_MAGIC_VALUE = 1.2
SAMPLE_SECONDS = 2

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
            
        rgb_mat = cv2.cvtColor(mat, cv2.COLOR_BGR2RGB)
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
            "message": "Image processed successfully"
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
                mat = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                filter_matrix_indexes.append(count) 
                filter_matrices.append(get_filter_matrix(mat))
                
                if progress_callback:
                    progress_callback({
                        "stage": "analyzing",
                        "progress": (count / frame_count) * 50,  # Анализ занимает 50% времени
                        "frames_processed": count,
                        "total_frames": frame_count
                    })
        
        cap.release()

        filter_matrices = np.array(filter_matrices)
        
        return {
            "input_video_path": input_video_path,
            "output_video_path": output_video_path,
            "fps": fps,
            "frame_count": count,
            "filters": filter_matrices,
            "filter_indices": filter_matrix_indexes
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

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        new_video = cv2.VideoWriter(
            video_data["output_video_path"], 
            fourcc, 
            video_data["fps"], 
            (int(frame_width), int(frame_height))
        )

        filter_matrices = video_data["filters"]
        filter_indices = video_data["filter_indices"]

        def get_interpolated_filter_matrix(frame_number):
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

            # Применяем фильтр
            rgb_mat = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
            "message": "Video processed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise

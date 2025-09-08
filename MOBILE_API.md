# Мобильный API для обработки видео и изображений

## Обзор

API оптимизирован для использования мобильными клиентами. Убраны все GUI зависимости и визуальные элементы, добавлены специальные мобильные endpoints с упрощенными ответами.

## Основные изменения для мобильного использования

### ✅ Убраны GUI зависимости:
- `opencv-python` → `opencv-python-headless`
- Удалены GUI библиотеки из Dockerfile
- Убраны preview данные из ответов API

### ✅ Добавлены мобильные endpoints:
- `/api/mobile/status` - статус API
- `/api/mobile/health` - быстрая проверка здоровья
- `/api/mobile/process/image` - обработка изображений
- `/api/mobile/files` - список файлов

### ✅ Оптимизированы ответы:
- Упрощенная структура JSON
- Убраны preview данные
- Добавлены прямые ссылки для скачивания
- Стандартизированные ответы с `success`/`error`

## API Endpoints

### Статус и здоровье

#### `GET /api/mobile/status`
Получает статус API и поддерживаемые функции.

**Ответ:**
```json
{
  "status": "online",
  "version": "1.0.0",
  "features": {
    "image_processing": true,
    "video_processing": true,
    "file_download": true,
    "progress_tracking": true
  },
  "supported_formats": {
    "images": ["jpg", "jpeg", "png", "bmp"],
    "videos": ["mp4", "avi", "mov", "mkv"]
  }
}
```

#### `GET /api/mobile/health`
Быстрая проверка здоровья API.

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Обработка изображений

#### `POST /api/mobile/process/image`
Обрабатывает изображение для коррекции цветов.

**Заголовки:**
```
Content-Type: multipart/form-data
```

**Параметры:**
- `file` - файл изображения (jpg, jpeg, png, bmp)

**Ответ при успехе:**
```json
{
  "success": true,
  "data": {
    "status": "success",
    "input_filename": "original.jpg",
    "output_filename": "original_corrected.jpg",
    "file_size": 1024000,
    "message": "Image processed successfully"
  }
}
```

**Ответ при ошибке:**
```json
{
  "success": false,
  "error": "Error message"
}
```

### Обработка видео

#### `POST /api/process/video`
Обрабатывает видео с streaming прогрессом.

**Заголовки:**
```
Content-Type: multipart/form-data
```

**Параметры:**
- `file` - файл видео (mp4, avi, mov, mkv)

**Ответ (Server-Sent Events):**
```
data: {"stage": "analyzing", "progress": 25.0, "frames_processed": 100, "total_frames": 400}

data: {"stage": "processing", "progress": 75.0, "frames_processed": 300, "total_frames": 400}

data: {"status": "success", "output_filename": "video_corrected.mp4", "file_size": 5000000}
```

### Управление файлами

#### `GET /api/mobile/files`
Получает список обработанных файлов.

**Ответ:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "filename": "image_corrected.jpg",
        "size": 1024000,
        "download_url": "/api/download/image_corrected.jpg"
      }
    ],
    "count": 1
  }
}
```

#### `GET /api/download/{filename}`
Скачивает обработанный файл.

**Ответ:** Бинарный файл

## Примеры использования

### JavaScript (React Native / Web)

```javascript
// Проверка статуса
const checkStatus = async () => {
  const response = await fetch('http://your-server:8000/api/mobile/status');
  const data = await response.json();
  console.log('API Status:', data.status);
};

// Обработка изображения
const processImage = async (imageFile) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  const response = await fetch('http://your-server:8000/api/mobile/process/image', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  if (result.success) {
    console.log('Image processed:', result.data.output_filename);
  } else {
    console.error('Error:', result.error);
  }
};

// Обработка видео с прогрессом
const processVideo = async (videoFile) => {
  const formData = new FormData();
  formData.append('file', videoFile);
  
  const response = await fetch('http://your-server:8000/api/process/video', {
    method: 'POST',
    body: formData
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          console.log('Progress:', data.progress + '%');
        } catch (e) {
          // Игнорируем некорректные JSON
        }
      }
    }
  }
};
```

### Swift (iOS)

```swift
// Обработка изображения
func processImage(imageData: Data) async throws {
    let url = URL(string: "http://your-server:8000/api/mobile/process/image")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    
    let boundary = UUID().uuidString
    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
    
    var body = Data()
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
    body.append(imageData)
    body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
    
    request.httpBody = body
    
    let (data, _) = try await URLSession.shared.data(for: request)
    let result = try JSONDecoder().decode(APIResponse.self, from: data)
    
    if result.success {
        print("Image processed: \(result.data.outputFilename)")
    } else {
        print("Error: \(result.error)")
    }
}
```

### Kotlin (Android)

```kotlin
// Обработка изображения
suspend fun processImage(imageFile: File) {
    val client = OkHttpClient()
    val requestBody = MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart("file", imageFile.name,
            imageFile.asRequestBody("image/jpeg".toMediaType()))
        .build()
    
    val request = Request.Builder()
        .url("http://your-server:8000/api/mobile/process/image")
        .post(requestBody)
        .build()
    
    client.newCall(request).execute().use { response ->
        if (response.isSuccessful) {
            val result = Gson().fromJson(response.body?.string(), ApiResponse::class.java)
            if (result.success) {
                println("Image processed: ${result.data.outputFilename}")
            } else {
                println("Error: ${result.error}")
            }
        }
    }
}
```

## Доступ

API доступен без авторизации для упрощения использования мобильными клиентами.

## Обработка ошибок

API возвращает стандартизированные ответы:

**Успех:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Ошибка:**
```json
{
  "success": false,
  "error": "Error message"
}
```

## Ограничения

- Максимальный размер файла: 500MB
- Поддерживаемые форматы изображений: JPG, JPEG, PNG, BMP
- Поддерживаемые форматы видео: MP4, AVI, MOV, MKV
- Автоматическое удаление файлов старше 7 дней

## Мониторинг

Для мониторинга API используйте:
- `GET /api/mobile/health` - быстрая проверка
- `GET /api/mobile/status` - детальная информация
- Логи сервера: `docker-compose logs -f`

# Android Integration Guide

Инструкция по интеграции Python API Server с Android приложением для обработки изображений и видео с коррекцией цветов.

## 📱 API Endpoints

**Базовый URL:** `http://95.81.76.7:8000`

### Основные endpoints:

- **Статус API:** `GET /api/mobile/status`
- **Health Check:** `GET /api/mobile/health`
- **Обработка изображения:** `POST /api/mobile/process/image`
- **Обработка видео:** `POST /api/mobile/process/video`
- **Список файлов:** `GET /api/mobile/files`
- **Скачивание файла:** `GET /api/download/{filename}`

## 🔧 Android Implementation

### 1. Добавление зависимостей

В `build.gradle` (Module: app):

```gradle
dependencies {
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.squareup.okhttp3:okhttp:4.11.0'
    implementation 'com.squareup.okhttp3:logging-interceptor:4.11.0'
    implementation 'androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0'
    implementation 'androidx.lifecycle:lifecycle-livedata-ktx:2.7.0'
    implementation 'androidx.activity:activity-ktx:1.8.2'
    implementation 'androidx.fragment:fragment-ktx:1.6.2'
}
```

### 2. Интернет разрешения

В `AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

### 3. Network Security Config

Создайте `res/xml/network_security_config.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">95.81.76.7</domain>
    </domain-config>
</network-security-config>
```

Добавьте в `AndroidManifest.xml`:

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ... >
```

### 4. API Models

Создайте `ApiModels.kt`:

```kotlin
data class ApiResponse<T>(
    val success: Boolean,
    val data: T? = null,
    val error: String? = null
)

data class StatusResponse(
    val status: String,
    val version: String,
    val features: Features
)

data class Features(
    val image_processing: Boolean,
    val video_processing: Boolean,
    val file_download: Boolean,
    val progress_tracking: Boolean
)

data class ProcessResponse(
    val status: String,
    val input_path: String,
    val output_path: String,
    val message: String,
    val input_filename: String,
    val output_filename: String,
    val file_size: Long
)

data class FileInfo(
    val filename: String,
    val size: Long,
    val download_url: String
)

data class FilesResponse(
    val files: List<FileInfo>,
    val count: Int
)
```

### 5. API Service

Создайте `ApiService.kt`:

```kotlin
import okhttp3.MultipartBody
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    
    @GET("api/mobile/status")
    suspend fun getStatus(): Response<ApiResponse<StatusResponse>>
    
    @GET("api/mobile/health")
    suspend fun getHealth(): Response<ApiResponse<Map<String, String>>>
    
    @Multipart
    @POST("api/mobile/process/image")
    suspend fun processImage(
        @Part file: MultipartBody.Part
    ): Response<ApiResponse<ProcessResponse>>
    
    @Multipart
    @POST("api/mobile/process/video")
    suspend fun processVideo(
        @Part file: MultipartBody.Part
    ): Response<ResponseBody>
    
    @GET("api/mobile/files")
    suspend fun getFiles(): Response<ApiResponse<FilesResponse>>
    
    @GET("api/download/{filename}")
    suspend fun downloadFile(
        @Path("filename") filename: String
    ): Response<ResponseBody>
}
```

### 6. Retrofit Client

Создайте `ApiClient.kt`:

```kotlin
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {
    private const val BASE_URL = "http://95.81.76.7:8000/"
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
    
    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val apiService: ApiService = retrofit.create(ApiService::class.java)
}
```

### 7. Repository

Создайте `ApiRepository.kt`:

```kotlin
import android.content.Context
import android.net.Uri
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream

class ApiRepository(private val context: Context) {
    
    private val apiService = ApiClient.apiService
    
    suspend fun getStatus(): Flow<Result<StatusResponse>> = flow {
        try {
            val response = apiService.getStatus()
            if (response.isSuccessful) {
                val apiResponse = response.body()
                if (apiResponse?.success == true && apiResponse.data != null) {
                    emit(Result.success(apiResponse.data))
                } else {
                    emit(Result.failure(Exception(apiResponse?.error ?: "Unknown error")))
                }
            } else {
                emit(Result.failure(Exception("HTTP ${response.code()}: ${response.message()}")))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }.flowOn(Dispatchers.IO)
    
    suspend fun processImage(imageUri: Uri): Flow<Result<ProcessResponse>> = flow {
        try {
            val file = File(context.cacheDir, "temp_image.jpg")
            context.contentResolver.openInputStream(imageUri)?.use { inputStream ->
                FileOutputStream(file).use { outputStream ->
                    inputStream.copyTo(outputStream)
                }
            }
            
            val requestFile = file.asRequestBody("image/jpeg".toMediaTypeOrNull())
            val body = MultipartBody.Part.createFormData("file", file.name, requestFile)
            
            val response = apiService.processImage(body)
            if (response.isSuccessful) {
                val apiResponse = response.body()
                if (apiResponse?.success == true && apiResponse.data != null) {
                    emit(Result.success(apiResponse.data))
                } else {
                    emit(Result.failure(Exception(apiResponse?.error ?: "Unknown error")))
                }
            } else {
                emit(Result.failure(Exception("HTTP ${response.code()}: ${response.message()}")))
            }
            
            file.delete()
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }.flowOn(Dispatchers.IO)
    
    suspend fun processVideo(videoUri: Uri): Flow<String> = flow {
        try {
            val file = File(context.cacheDir, "temp_video.mp4")
            context.contentResolver.openInputStream(videoUri)?.use { inputStream ->
                FileOutputStream(file).use { outputStream ->
                    inputStream.copyTo(outputStream)
                }
            }
            
            val requestFile = file.asRequestBody("video/mp4".toMediaTypeOrNull())
            val body = MultipartBody.Part.createFormData("file", file.name, requestFile)
            
            val response = apiService.processVideo(body)
            if (response.isSuccessful) {
                response.body()?.byteStream()?.use { inputStream ->
                    val reader = inputStream.bufferedReader()
                    reader.lineSequence().forEach { line ->
                        if (line.startsWith("data: ")) {
                            val jsonData = line.substring(6)
                            emit(jsonData)
                        }
                    }
                }
            } else {
                emit("error: HTTP ${response.code()}: ${response.message()}")
            }
            
            file.delete()
        } catch (e: Exception) {
            emit("error: ${e.message}")
        }
    }.flowOn(Dispatchers.IO)
    
    suspend fun getFiles(): Flow<Result<List<FileInfo>>> = flow {
        try {
            val response = apiService.getFiles()
            if (response.isSuccessful) {
                val apiResponse = response.body()
                if (apiResponse?.success == true && apiResponse.data != null) {
                    emit(Result.success(apiResponse.data.files))
                } else {
                    emit(Result.failure(Exception(apiResponse?.error ?: "Unknown error")))
                }
            } else {
                emit(Result.failure(Exception("HTTP ${response.code()}: ${response.message()}")))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }.flowOn(Dispatchers.IO)
    
    suspend fun downloadFile(filename: String): Flow<Result<File>> = flow {
        try {
            val response = apiService.downloadFile(filename)
            if (response.isSuccessful) {
                val file = File(context.getExternalFilesDir(null), filename)
                response.body()?.byteStream()?.use { inputStream ->
                    FileOutputStream(file).use { outputStream ->
                        inputStream.copyTo(outputStream)
                    }
                }
                emit(Result.success(file))
            } else {
                emit(Result.failure(Exception("HTTP ${response.code()}: ${response.message()}")))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }.flowOn(Dispatchers.IO)
}
```

### 8. ViewModel

Создайте `MainViewModel.kt`:

```kotlin
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class MainViewModel(private val repository: ApiRepository) : ViewModel() {
    
    private val _status = MutableStateFlow<Result<StatusResponse>?>(null)
    val status: StateFlow<Result<StatusResponse>?> = _status.asStateFlow()
    
    private val _processingResult = MutableStateFlow<Result<ProcessResponse>?>(null)
    val processingResult: StateFlow<Result<ProcessResponse>?> = _processingResult.asStateFlow()
    
    private val _videoProgress = MutableStateFlow<String?>(null)
    val videoProgress: StateFlow<String?> = _videoProgress.asStateFlow()
    
    private val _files = MutableStateFlow<Result<List<FileInfo>>?>(null)
    val files: StateFlow<Result<List<FileInfo>>?> = _files.asStateFlow()
    
    fun checkStatus() {
        viewModelScope.launch {
            repository.getStatus().collect { result ->
                _status.value = result
            }
        }
    }
    
    fun processImage(imageUri: Uri) {
        viewModelScope.launch {
            repository.processImage(imageUri).collect { result ->
                _processingResult.value = result
            }
        }
    }
    
    fun processVideo(videoUri: Uri) {
        viewModelScope.launch {
            repository.processVideo(videoUri).collect { progress ->
                _videoProgress.value = progress
            }
        }
    }
    
    fun getFiles() {
        viewModelScope.launch {
            repository.getFiles().collect { result ->
                _files.value = result
            }
        }
    }
}
```

### 9. Activity Example

Пример использования в `MainActivity.kt`:

```kotlin
import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    
    private val viewModel: MainViewModel by viewModels {
        MainViewModelFactory(ApiRepository(this))
    }
    
    private val imagePickerLauncher = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri ->
        uri?.let { viewModel.processImage(it) }
    }
    
    private val videoPickerLauncher = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri ->
        uri?.let { viewModel.processVideo(it) }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        checkPermissions()
        observeViewModel()
        viewModel.checkStatus()
    }
    
    private fun checkPermissions() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE)
            != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE), 1)
        }
    }
    
    private fun observeViewModel() {
        lifecycleScope.launch {
            viewModel.status.collect { result ->
                result?.fold(
                    onSuccess = { status ->
                        Toast.makeText(this@MainActivity, 
                            "API Status: ${status.status}", Toast.LENGTH_SHORT).show()
                    },
                    onFailure = { error ->
                        Toast.makeText(this@MainActivity, 
                            "Error: ${error.message}", Toast.LENGTH_SHORT).show()
                    }
                )
            }
        }
        
        lifecycleScope.launch {
            viewModel.processingResult.collect { result ->
                result?.fold(
                    onSuccess = { response ->
                        Toast.makeText(this@MainActivity, 
                            "Image processed: ${response.output_filename}", Toast.LENGTH_SHORT).show()
                    },
                    onFailure = { error ->
                        Toast.makeText(this@MainActivity, 
                            "Processing error: ${error.message}", Toast.LENGTH_SHORT).show()
                    }
                )
            }
        }
        
        lifecycleScope.launch {
            viewModel.videoProgress.collect { progress ->
                progress?.let {
                    if (it.startsWith("error:")) {
                        Toast.makeText(this@MainActivity, it, Toast.LENGTH_SHORT).show()
                    } else {
                        // Обновить прогресс-бар
                        println("Video progress: $it")
                    }
                }
            }
        }
    }
    
    private fun selectImage() {
        imagePickerLauncher.launch("image/*")
    }
    
    private fun selectVideo() {
        videoPickerLauncher.launch("video/*")
    }
}
```

## 🔧 Настройки

### Base URL
```kotlin
private const val BASE_URL = "http://95.81.76.7:8000/"
```

### Поддерживаемые форматы
- **Изображения:** JPG, JPEG, PNG, BMP
- **Видео:** MP4, AVI, MOV, MKV

### Таймауты
- **Подключение:** 30 секунд
- **Чтение/Запись:** 60 секунд

## ⚠️ Важные замечания

1. **Без авторизации:** API работает без токенов для упрощения
2. **HTTP:** Используется HTTP (не HTTPS) для тестирования
3. **CORS:** Настроен для всех доменов (`*`)
4. **Прогресс видео:** Используется Server-Sent Events (SSE)

## 🚀 Готово к использованию!

API полностью настроен и готов к интеграции с Android приложением.

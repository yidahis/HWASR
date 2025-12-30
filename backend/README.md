# Whisper ASR 后端服务

基于 FastAPI 的语音识别后端服务，集成 Whisper-large-v3-turbo 模型和 WhisperX 说话人识别功能。

## 环境要求

- Python 3.10+
- FFmpeg
- CUDA 11.8+ (可选，用于 GPU 加速)

## 安装

1. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 安装 FFmpeg
- Ubuntu/Debian: `sudo apt-get install ffmpeg`
- macOS: `brew install ffmpeg`
- Windows: 从 https://ffmpeg.org/download.html 下载

## 配置

复制 `.env.example` 为 `.env` 并根据需要修改配置：

```bash
cp .env.example .env
```

## 运行

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### POST /api/upload
上传音频文件并启动识别任务

**请求**: multipart/form-data
- file: 音频文件 (WAV, MP3, M4A, FLAC, OGG, AAC)

**响应**: TaskStatus
```json
{
  "task_id": "uuid",
  "status": "pending",
  "progress": 0.0,
  "message": "文件上传成功，开始处理"
}
```

### GET /api/status/{task_id}
查询任务状态

**响应**: TaskStatus
```json
{
  "task_id": "uuid",
  "status": "completed",
  "progress": 100.0,
  "message": "识别完成",
  "result_id": "result_uuid"
}
```

### GET /api/result/{result_id}
获取识别结果

**响应**: ASRResult
```json
{
  "success": true,
  "result_id": "uuid",
  "text": "完整转录文本",
  "sentences": [...],
  "speakers": [0, 1, 2],
  "total_duration": 317.22,
  "audio_hash": "sha256_hash",
  "filename": "original.mp3",
  "timestamp": "2025-12-30T14:34:47.553383Z",
  "message": "Recognition completed successfully",
  "audio_path": "result_uuid_audio.wav"
}
```

### GET /api/audio/{result_id}
获取识别后的音频文件

### GET /api/download/{result_id}
下载识别结果 JSON 文件

## 目录结构

```
backend/
├── app/
│   ├── api/
│   │   └── routes.py           # API 路由
│   ├── core/
│   │   └── config.py           # 配置文件
│   ├── models/
│   │   └── schemas.py          # Pydantic 模型
│   ├── services/
│   │   ├── whisper_service.py   # Whisper 服务
│   │   ├── diarization_service.py  # WhisperX 服务
│   │   ├── translation_service.py  # 翻译服务
│   │   └── task_manager.py     # 任务管理
│   ├── utils/
│   │   ├── helpers.py          # 工具函数
│   │   └── audio_processor.py  # 音频处理
│   └── main.py                # 应用入口
├── storage/
│   ├── uploads/                # 原始上传文件
│   ├── processed/              # 处理后的音频
│   └── results/               # JSON 结果
├── requirements.txt
├── .env.example
└── README.md
```

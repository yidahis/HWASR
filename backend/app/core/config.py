import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'uploads')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'results')
AUDIO_PROCESSED_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'processed')

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(AUDIO_PROCESSED_DIR, exist_ok=True)

# 模型配置
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "large-v3-turbo")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "int8")

# WhisperX 配置
ENABLE_DIARIZATION = os.getenv("ENABLE_DIARIZATION", "true").lower() == "true"
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN", None)

# 翻译服务配置
TRANSLATION_ENABLED = os.getenv("TRANSLATION_ENABLED", "true").lower() == "true"
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", None)

# API 配置
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac']

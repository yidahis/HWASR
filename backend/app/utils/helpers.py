import hashlib
import os
from datetime import datetime
from typing import Optional
import uuid
import aiofiles


async def calculate_audio_hash(file_path: str) -> str:
    """计算音频文件的 SHA256 哈希值"""
    sha256_hash = hashlib.sha256()
    async with aiofiles.open(file_path, 'rb') as f:
        while chunk := await f.read(8192):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def generate_result_id() -> str:
    """生成唯一的结果 ID"""
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """获取当前时间戳字符串"""
    return datetime.utcnow().isoformat() + 'Z'


def ensure_directory(directory: str) -> None:
    """确保目录存在"""
    os.makedirs(directory, exist_ok=True)


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    return os.path.getsize(file_path)


def format_timestamp(seconds: float) -> str:
    """将秒数格式化为时间戳字符串 (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

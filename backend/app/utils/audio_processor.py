from pydub import AudioSegment
import os
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


async def convert_to_wav(input_path: str, output_path: str) -> Tuple[str, float]:
    """
    将音频文件转换为 16kHz 单声道 WAV 格式
    返回: (输出路径, 持续时间(秒))
    """
    try:
        audio = AudioSegment.from_file(input_path)
        
        # 转换为单声道
        audio = audio.set_channels(1)
        
        # 重采样到 16kHz
        audio = audio.set_frame_rate(16000)
        
        # 导出为 WAV
        audio.export(output_path, format="wav")
        
        duration = len(audio) / 1000.0  # 毫秒转秒
        
        logger.info(f"音频转换完成: {input_path} -> {output_path}, 时长: {duration:.2f}秒")
        return output_path, duration
        
    except Exception as e:
        logger.error(f"音频转换失败: {e}")
        raise


def get_audio_duration(file_path: str) -> float:
    """获取音频文件时长（秒）"""
    audio = AudioSegment.from_file(file_path)
    return len(audio) / 1000.0


def is_valid_audio_file(file_path: str) -> bool:
    """检查是否为有效的音频文件"""
    valid_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac']
    ext = os.path.splitext(file_path)[1].lower()
    return ext in valid_extensions

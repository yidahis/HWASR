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

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

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


def trim_audio(
    input_path: str,
    output_path: str,
    start_time: float = None,
    end_time: float = None
) -> Tuple[str, float]:
    """
    剪切音频文件

    Args:
        input_path: 输入音频文件路径
        output_path: 输出音频文件路径
        start_time: 开始时间（秒），None 表示从头开始
        end_time: 结束时间（秒），None 表示到文件末尾

    Returns:
        (输出路径, 持续时间(秒))

    Raises:
        ValueError: 当时间参数无效时
    """
    try:
        audio = AudioSegment.from_file(input_path)

        # 验证时间参数
        duration = len(audio) / 1000.0

        if start_time is not None and start_time < 0:
            raise ValueError(f"开始时间不能为负数: {start_time}")

        if end_time is not None and end_time > duration:
            logger.warning(f"结束时间 {end_time} 超过音频时长 {duration}，将使用音频末尾")
            end_time = duration

        if start_time is not None and end_time is not None and start_time >= end_time:
            raise ValueError(f"开始时间 {start_time} 必须小于结束时间 {end_time}")

        # 转换为毫秒
        start_ms = int(start_time * 1000) if start_time is not None else 0
        end_ms = int(end_time * 1000) if end_time is not None else len(audio)

        # 剪切音频
        trimmed_audio = audio[start_ms:end_ms]

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 导出剪切后的音频
        trimmed_audio.export(output_path, format="wav")

        new_duration = len(trimmed_audio) / 1000.0

        logger.info(f"音频剪切完成: {input_path} -> {output_path}, 原始时长: {duration:.2f}秒, 剪切后: {new_duration:.2f}秒")
        return output_path, new_duration

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"音频剪切失败: {e}")
        raise

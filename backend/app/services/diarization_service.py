import logging
import torch
import numpy as np
from typing import List, Dict, Any
import sys
import os
from ..core.config import HF_TOKEN

logger = logging.getLogger(__name__)

# Monkey patch for torchaudio to fix compatibility with newer versions
# Must be done before importing pyannote.audio
import torchaudio

# 创建 torchaudio.backend 模块以兼容旧版 API
if 'torchaudio.backend' not in sys.modules:
    # 创建动态模块
    import types
    torchaudio_backend_module = types.ModuleType('torchaudio.backend')
    torchaudio_common_module = types.ModuleType('torchaudio.backend.common')

    # 添加 AudioMetaData 类
    class AudioMetaData:
        def __init__(self):
            pass

    torchaudio_common_module.AudioMetaData = AudioMetaData
    sys.modules['torchaudio.backend'] = torchaudio_backend_module
    sys.modules['torchaudio.backend.common'] = torchaudio_common_module
    logger.info("已为 torchaudio 添加 backend 模块兼容性补丁")

if not hasattr(torchaudio, 'set_audio_backend'):
    torchaudio.set_audio_backend = lambda backend: None
    logger.info("已为 torchaudio 添加 set_audio_backend 兼容性补丁")

if not hasattr(torchaudio, 'get_audio_backend'):
    torchaudio.get_audio_backend = lambda: None
    logger.info("已为 torchaudio 添加 get_audio_backend 兼容性补丁")

if not hasattr(torchaudio, 'list_audio_backends'):
    torchaudio.list_audio_backends = lambda: []
    logger.info("已为 torchaudio 添加 list_audio_backends 兼容性补丁")

# Monkey patch for numpy 2.0 compatibility with pyannote.audio
# NumPy 2.0 removed np.NaN and np.NAN, but pyannote.audio still uses them
if not hasattr(np, 'NaN'):
    np.NaN = np.nan
    logger.info("已为 numpy 添加 np.NaN 兼容性补丁")
if not hasattr(np, 'NAN'):
    np.NAN = np.nan
    logger.info("已为 numpy 添加 np.NAN 兼容性补丁")

# Monkey patch for PyTorch 2.6+ weights_only compatibility
# PyTorch 2.6 changed default weights_only from False to True
# This breaks loading of pyannote.audio models
original_torch_load = torch.load

def patched_torch_load(f, *args, **kwargs):
    # Set weights_only=False by default for compatibility
    kwargs.setdefault('weights_only', False)
    return original_torch_load(f, *args, **kwargs)

torch.load = patched_torch_load
logger.info("已为 torch.load 添加 weights_only 兼容性补丁")

# Add safe globals for PyTorch 2.6+ serialization
if hasattr(torch, 'serialization'):
    try:
        if hasattr(torch.torch_version, 'TorchVersion'):
            torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])
            logger.info("已为 torch.serialization 添加 TorchVersion 安全全局变量")
    except Exception:
        pass

class DiarizationService:
    def __init__(self):
        self.model = None
        self.pipeline = None

    def load_model(self):
        """延迟加载说话人识别模型"""
        if self.model is not None:
            return

        if not HF_TOKEN:
            logger.warning("未设置 HUGGINGFACE_TOKEN，说话人识别功能不可用")
            return

        try:
            from pyannote.audio import Pipeline
            logger.info("正在加载 pyannote.audio 说话人识别模型...")

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"使用设备: {device}")

            # 设置环境变量以禁用 PyTorch 2.6+ 的 weights_only 安全检查
            # pyannote.audio 模型包含旧版的 pickle 对象，不兼容 weights_only=True
            old_env = os.environ.get('TORCH_DISABLE_WEIGHTS_ONLY_LOAD')
            os.environ['TORCH_DISABLE_WEIGHTS_ONLY_LOAD'] = '1'

            try:
                # 直接使用 pyannote.audio 的说话人识别
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=HF_TOKEN
                )
                self.pipeline.to(device)

                logger.info("pyannote.audio 模型加载完成")
            finally:
                # 恢复环境变量
                if old_env is None:
                    os.environ.pop('TORCH_DISABLE_WEIGHTS_ONLY_LOAD', None)
                else:
                    os.environ['TORCH_DISABLE_WEIGHTS_ONLY_LOAD'] = old_env

        except ImportError as e:
            logger.error(f"pyannote.audio 导入失败: {e}")
            logger.warning("请安装: pip install pyannote.audio")
            self.model = None
        except Exception as e:
            logger.error(f"加载说话人识别模型失败: {e}")
            self.model = None

    def assign_speakers(
        self,
        audio_path: str,
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        为 Whisper 识别的片段分配说话人标签

        参数:
            audio_path: 音频文件路径
            segments: Whisper 识别的片段列表

        返回:
            带有 speaker 信息的片段列表
        """
        try:
            if self.pipeline is None:
                self.load_model()

            if self.pipeline is None:
                logger.warning("说话人识别模型未加载，分配默认说话人")
                for seg in segments:
                    seg["speaker"] = 0
                return segments

            logger.info("开始说话人识别...")

            # 执行说话人分离
            diarization = self.pipeline(audio_path)

            # 将说话人分配到片段
            result = self._assign_speakers_to_segments(segments, diarization)

            # 统计说话人数量
            unique_speakers = set(seg["speaker"] for seg in result)
            logger.info(f"说话人识别完成，识别到 {len(unique_speakers)} 个说话人")

            return result

        except Exception as e:
            logger.error(f"说话人识别失败: {e}", exc_info=True)
            logger.warning("分配默认说话人标签")
            for seg in segments:
                seg["speaker"] = 0
            return segments

    def _assign_speakers_to_segments(
        self,
        segments: List[Dict[str, Any]],
        diarization: Any
    ) -> List[Dict[str, Any]]:
        """
        将说话人分配到 Whisper 识别的片段

        参数:
            segments: Whisper 识别的片段
            diarization: pyannote.audio 说话人分离结果

        返回:
            带有说话人标签的片段列表
        """
        # 创建说话人 ID 映射
        speaker_map = {}
        speaker_id_counter = 0

        # 遍历每个文本片段
        for seg in segments:
            seg_start = seg["start"]
            seg_end = seg["end"]
            seg_mid = (seg_start + seg_end) / 2

            # 找到与片段中点重叠的说话人
            best_speaker = None
            best_duration = 0

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                turn_start = turn.start
                turn_end = turn.end

                # 计算重叠时间
                overlap_start = max(seg_start, turn_start)
                overlap_end = min(seg_end, turn_end)
                overlap_duration = max(0, overlap_end - overlap_start)

                if overlap_duration > best_duration:
                    best_duration = overlap_duration
                    best_speaker = speaker

            # 分配或映射说话人 ID
            if best_speaker is not None:
                if best_speaker not in speaker_map:
                    speaker_map[best_speaker] = speaker_id_counter
                    speaker_id_counter += 1
                seg["speaker"] = speaker_map[best_speaker]
            else:
                seg["speaker"] = 0

        return segments


# 全局实例
diarization_service = DiarizationService()

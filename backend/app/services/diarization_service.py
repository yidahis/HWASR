# ---------------------------------------------------------------------------
# 关键：必须在导入任何模块之前设置环境变量
# ---------------------------------------------------------------------------
import os

# 设置 HuggingFace 离线模式 - 必须在任何 huggingface_hub 导入之前设置
os.environ.setdefault("HF_HUB_OFFLINE", "1")

# 设置 HuggingFace 缓存目录
if not os.environ.get('HF_HOME'):
    hf_cache = os.path.expanduser('~/.cache/huggingface')
    os.environ['HF_HOME'] = hf_cache
    os.environ['HUGGINGFACE_HUB_CACHE'] = os.path.join(hf_cache, 'hub')

# 设置 torchaudio 使用 soundfile 后端
os.environ.setdefault("TORCHAUDIO_USE_CODEC_BACKEND", "0")

# 现在可以安全地导入其他模块
import logging
import torch
import numpy as np
from typing import List, Dict, Any
import sys
from ..core.config import HF_TOKEN

logger = logging.getLogger(__name__)

logger.info("已设置 HF_HUB_OFFLINE=1，强制使用本地缓存（离线模式）")
hf_cache_dir = os.environ.get('HF_HOME', os.path.expanduser('~/.cache/huggingface'))
logger.info(f"已设置 HuggingFace 缓存目录: {hf_cache_dir}")
logger.info("已设置 TORCHAUDIO_USE_CODEC_BACKEND=0，禁用 torchcodec 后端")

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

# PyTorch 2.6+ 移除了 AudioMetaData，直接添加到 torchaudio
if not hasattr(torchaudio, 'AudioMetaData'):
    class AudioMetaData:
        def __init__(self):
            pass
    torchaudio.AudioMetaData = AudioMetaData
    logger.info("已为 torchaudio 添加 AudioMetaData 兼容性补丁")

if not hasattr(torchaudio, 'set_audio_backend'):
    torchaudio.set_audio_backend = lambda backend: None
    logger.info("已为 torchaudio 添加 set_audio_backend 兼容性补丁")

if not hasattr(torchaudio, 'get_audio_backend'):
    torchaudio.get_audio_backend = lambda: None
    logger.info("已为 torchaudio 添加 get_audio_backend 兼容性补丁")

if not hasattr(torchaudio, 'list_audio_backends'):
    torchaudio.list_audio_backends = lambda: ["soundfile", "sox_io"]
    logger.info("已为 torchaudio 添加 list_audio_backends 兼容性补丁")

# Add torchaudio.info compatibility patch for torchaudio 2.6+
if not hasattr(torchaudio, 'info'):
    def torchaudio_info(uri, *args, **kwargs):
        """Provide torchaudio.info functionality using soundfile library"""
        try:
            import soundfile

            # Get audio file info using soundfile
            logger.debug(f"使用 soundfile 库获取音频信息: {uri}")
            info = soundfile.info(uri)

            # Create an AudioMetaData-like object
            class AudioMetaData:
                def __init__(self, sample_rate, num_frames, num_channels, bits_per_sample, encoding, format):
                    self.sample_rate = sample_rate
                    self.num_frames = num_frames
                    self.num_channels = num_channels
                    self.bits_per_sample = bits_per_sample
                    self.encoding = encoding
                    self.format = format

            return AudioMetaData(
                sample_rate=info.samplerate,
                num_frames=info.frames,
                num_channels=info.channels,
                bits_per_sample=info.subtype.split('_')[0] if '_' in info.subtype else '16',
                encoding='PCM_S',
                format=info.format.upper()
            )
        except Exception as e:
            logger.debug(f"soundfile 库获取信息失败: {e}")
            raise

    torchaudio.info = torchaudio_info
    logger.info("已为 torchaudio 添加 info 兼容性补丁")

# Monkey patch torchaudio.load to force using soundfile backend
# This fixes the torchcodec bug in torchaudio 2.6+
if hasattr(torchaudio, 'load'):
    original_torchaudio_load = torchaudio.load

    def patched_torchaudio_load(uri, *args, **kwargs):
        # Import soundfile library directly
        try:
            import soundfile

            # Load audio using soundfile library
            logger.debug(f"使用 soundfile 库加载音频: {uri}")
            data, sample_rate = soundfile.read(uri, dtype='float32')

            # Convert to torch tensor with shape (channels, samples)
            # Soundfile returns shape (samples,), we need (1, samples) for mono
            if len(data.shape) == 1:
                data = data.reshape(1, -1)
            else:
                data = data.T  # Convert from (samples, channels) to (channels, samples)

            # Convert to torch tensor
            waveform = torch.from_numpy(data)

            # Handle optional parameters
            frame_offset = kwargs.get('frame_offset', 0)
            num_frames = kwargs.get('num_frames', -1)

            if frame_offset > 0:
                waveform = waveform[:, frame_offset:]

            if num_frames > 0:
                waveform = waveform[:, :num_frames]

            # Handle normalize
            normalize = kwargs.get('normalize', True)
            if normalize:
                waveform = waveform / torch.max(torch.abs(waveform))

            # Handle channels_first (always true in our implementation)
            return waveform, sample_rate

        except Exception as e:
            logger.debug(f"soundfile 库加载失败: {e}, 尝试原始 torchaudio.load")
            # Fall back to original load
            return original_torchaudio_load(uri, *args, **kwargs)

    torchaudio.load = patched_torchaudio_load
    logger.info("已为 torchaudio.load 添加强制使用 soundfile 库的补丁")

# Patch torchcodec load function to use soundfile instead
try:
    from torchaudio import _torchcodec
    if hasattr(_torchcodec, 'load_with_torchcodec'):
        original_load_with_torchcodec = _torchcodec.load_with_torchcodec

        def patched_load_with_torchcodec(uri, *args, **kwargs):
            # Redirect to soundfile library
            logger.debug(f"torchcodec 被调用，重定向到 soundfile 库: {uri}")
            try:
                import soundfile
                import torch

                # Load audio using soundfile library
                data, sample_rate = soundfile.read(uri, dtype='float32')

                # Convert to torch tensor
                if len(data.shape) == 1:
                    data = data.reshape(1, -1)
                else:
                    data = data.T

                waveform = torch.from_numpy(data)

                return waveform, sample_rate
            except Exception as e:
                logger.debug(f"回退到 soundfile 库失败: {e}")
            # If all fails, raise the original error
            raise RuntimeError(f"torchcodec backend disabled, please use soundfile library")

        _torchcodec.load_with_torchcodec = patched_load_with_torchcodec
        logger.info("已为 _torchcodec.load_with_torchcodec 添加重定向到 soundfile 库的补丁")
except ImportError:
    pass

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
        # Add common pyannote.audio safe globals
        try:
            from pyannote.audio.core.task import Specifications, Problem, Resolution
            torch.serialization.add_safe_globals([Specifications, Problem, Resolution])
            logger.info("已为 torch.serialization 添加 Specifications, Problem, Resolution 安全全局变量")
        except ImportError:
            pass

        try:
            from pyannote.core import Annotation, Segment, SlidingWindow
            torch.serialization.add_safe_globals([Annotation, Segment, SlidingWindow])
            logger.info("已为 torch.serialization 添加 pyannote.core 安全全局变量")
        except ImportError:
            pass

        try:
            from pyannote.audio.core.model import Model
            torch.serialization.add_safe_globals([Model])
            logger.info("已为 torch.serialization 添加 Model 安全全局变量")
        except ImportError:
            pass

        if hasattr(torch.torch_version, 'TorchVersion'):
            torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])
            logger.info("已为 torch.serialization 添加 TorchVersion 安全全局变量")
    except Exception as e:
        logger.warning(f"添加安全全局变量时出错: {e}")

class DiarizationService:
    def __init__(self):
        self.model = None
        self.pipeline = None

    def load_model(self):
        """延迟加载说话人识别模型"""
        if self.model is not None:
            return

        try:
            from pyannote.audio import Pipeline
            logger.info("正在加载 pyannote.audio 说话人识别模型...")

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"使用设备: {device}")

            # 检查离线模式设置
            hf_offline = os.environ.get('HF_HUB_OFFLINE', '0')
            logger.info(f"HF_HUB_OFFLINE: {hf_offline}")

            # 设置环境变量以禁用 PyTorch 2.6+ 的 weights_only 安全检查
            # pyannote.audio 模型包含旧版的 pickle 对象，不兼容 weights_only=True
            old_weights_env = os.environ.get('TORCH_DISABLE_WEIGHTS_ONLY_LOAD')
            os.environ['TORCH_DISABLE_WEIGHTS_ONLY_LOAD'] = '1'

            try:
                # pyannote.audio 会自动使用 HuggingFace 缓存
                # HF_HUB_OFFLINE=1 已在模块级别设置，确保断网时使用本地缓存
                if HF_TOKEN:
                    logger.info("使用 HF_TOKEN 加载模型")
                    self.pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=HF_TOKEN
                    )
                else:
                    logger.info("不使用 HF_TOKEN 加载模型")
                    self.pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1"
                    )
                self.pipeline.to(device)

                logger.info("pyannote.audio 模型加载完成")
            finally:
                # 恢复环境变量
                if old_weights_env is None:
                    os.environ.pop('TORCH_DISABLE_WEIGHTS_ONLY_LOAD', None)
                else:
                    os.environ['TORCH_DISABLE_WEIGHTS_ONLY_LOAD'] = old_weights_env

        except ImportError as e:
            logger.error(f"pyannote.audio 导入失败: {e}")
            logger.warning("请安装: pip install pyannote.audio")
            self.model = None
        except Exception as e:
            logger.error(f"加载说话人识别模型失败: {e}", exc_info=True)
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

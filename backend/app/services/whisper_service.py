from faster_whisper import WhisperModel
import logging
from typing import List, Dict, Any
from ..core.config import WHISPER_MODEL_NAME, WHISPER_DEVICE, COMPUTE_TYPE

logger = logging.getLogger(__name__)


class WhisperService:
    def __init__(self):
        logger.info(f"正在加载 Whisper 模型: {WHISPER_MODEL_NAME}")
        self.model = WhisperModel(
            WHISPER_MODEL_NAME,
            device=WHISPER_DEVICE,
            compute_type=COMPUTE_TYPE
        )
        logger.info("Whisper 模型加载完成")
    
    def transcribe(self, audio_path: str, language: str = None) -> Dict[str, Any]:
        """
        执行语音识别
        返回格式化后的结果
        """
        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                word_timestamps=True,
                beam_size=5,
                vad_filter=True
            )
            
            result = {
                "text": "",
                "segments": [],
                "language": info.language
            }
            
            full_text = []
            for segment in segments:
                segment_data = {
                    "text": segment.text.strip(),
                    "start": segment.start,
                    "end": segment.end,
                    "words": []
                }
                
                if segment.words:
                    for word in segment.words:
                        segment_data["words"].append({
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability
                        })
                
                result["segments"].append(segment_data)
                full_text.append(segment.text.strip())
            
            result["text"] = " ".join(full_text)
            
            logger.info(f"识别完成，共 {len(result['segments'])} 个片段")
            return result
            
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            raise

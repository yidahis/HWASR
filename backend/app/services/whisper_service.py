from faster_whisper import WhisperModel
import logging
from typing import List, Dict, Any, Optional, Callable
from ..core.config import WHISPER_MODEL_NAME, WHISPER_DEVICE, COMPUTE_TYPE

logger = logging.getLogger(__name__)


class WhisperService:
    def __init__(self):
        logger.info(f"正在加载 Whisper 模型: {WHISPER_MODEL_NAME}")
        self.model = WhisperModel(
            WHISPER_MODEL_NAME,
            device=WHISPER_DEVICE,
            compute_type=COMPUTE_TYPE,
            local_files_only=True
        )
        logger.info("Whisper 模型加载完成")
    
    def _post_process_text(self, text: str) -> str:
        """
        后处理文本：改善大小写和标点符号
        """
        if not text:
            return text
        
        # 分割句子
        sentences = []
        current_sentence = []
        
        # 标点符号标记
        sentence_endings = ['.', '!', '?', '。', '！', '？']
        
        # 按字符处理
        for char in text:
            current_sentence.append(char)
            if char in sentence_endings:
                sentences.append(''.join(current_sentence))
                current_sentence = []
        
        # 添加剩余内容
        if current_sentence:
            sentences.append(''.join(current_sentence))
        
        # 处理每个句子
        processed_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # 句首字母大写
                if sentence[0].isalpha():
                    sentence = sentence[0].upper() + sentence[1:]
                
                # 将中文标点替换为英文标点
                sentence = sentence.replace('。', '.')
                sentence = sentence.replace('！', '!')
                sentence = sentence.replace('？', '?')
                sentence = sentence.replace('，', ',')
                sentence = sentence.replace('；', ';')
                sentence = sentence.replace('：', ':')
                
                processed_sentences.append(sentence)
        
        return ' '.join(processed_sentences)
    
    def transcribe(self, audio_path: str, language: str = None, progress_callback: Optional[Callable[[float], None]] = None) -> Dict[str, Any]:
        """
        执行语音识别
        返回格式化后的结果
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码（可选）
            progress_callback: 进度回调函数，接受进度百分比（0-100）
        """
        try:
            # 使用优化的参数改善识别结果
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                word_timestamps=True,
                beam_size=5,
                vad_filter=True,
                # 优化参数
                condition_on_previous_text=True,
                suppress_tokens=[],  # 不抑制任何token，保留标点和大小写
                prepend_punctuations="\"'([{<",
                append_punctuations="\"').。,!?;:]}>"
            )
            
            result = {
                "text": "",
                "segments": [],
                "language": info.language
            }
            
            full_text = []
            segment_count = 0
            total_duration = info.duration
            
            for segment in segments:
                segment_count += 1
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
                
                # 调用进度回调，基于当前识别进度
                if progress_callback and total_duration > 0:
                    progress = 50.0 + (segment.end / total_duration) * 15.0  # 50% -> 65%
                    progress_callback(min(progress, 65.0))
            
            result["text"] = " ".join(full_text)
            
            # 对文本进行后处理：句首大写和标点符号规范化
            result["text"] = self._post_process_text(result["text"])
            
            logger.info(f"识别完成，共 {len(result['segments'])} 个片段")
            return result
            
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            raise

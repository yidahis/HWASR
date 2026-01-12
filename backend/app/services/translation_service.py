import logging
import os
import torch
from typing import Dict, Any
from app.core.config import TRANSLATION_ENABLED

logger = logging.getLogger(__name__)


class TranslationService:
    """翻译服务 - 使用 MarianMT 实现离线中英文互译"""

    # 模型名称
    MODEL_EN_ZH = "Helsinki-NLP/opus-mt-en-zh"  # 英文 → 中文
    MODEL_ZH_EN = "Helsinki-NLP/opus-mt-zh-en"  # 中文 → 英文

    def __init__(self):
        self.enabled = TRANSLATION_ENABLED
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_en_zh = None
        self.tokenizer_en_zh = None
        self.model_zh_en = None
        self.tokenizer_zh_en = None
        logger.info(f"翻译服务初始化完成，使用设备: {self.device}")

    def _load_model_en_zh(self):
        """延迟加载英文→中文模型"""
        if self.model_en_zh is not None:
            return

        try:
            logger.info(f"正在加载 {self.MODEL_EN_ZH} 模型...")
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

            self.tokenizer_en_zh = AutoTokenizer.from_pretrained(
                self.MODEL_EN_ZH,
                local_files_only=True
            )
            self.model_en_zh = AutoModelForSeq2SeqLM.from_pretrained(
                self.MODEL_EN_ZH,
                local_files_only=True,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32
            ).to(self.device)

            logger.info(f"{self.MODEL_EN_ZH} 模型加载完成")

        except Exception as e:
            logger.error(f"加载 {self.MODEL_EN_ZH} 模型失败: {e}")
            self.model_en_zh = None
            self.tokenizer_en_zh = None

    def _load_model_zh_en(self):
        """延迟加载中文→英文模型"""
        if self.model_zh_en is not None:
            return

        try:
            logger.info(f"正在加载 {self.MODEL_ZH_EN} 模型...")
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

            self.tokenizer_zh_en = AutoTokenizer.from_pretrained(
                self.MODEL_ZH_EN,
                local_files_only=True
            )
            self.model_zh_en = AutoModelForSeq2SeqLM.from_pretrained(
                self.MODEL_ZH_EN,
                local_files_only=True,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32
            ).to(self.device)

            logger.info(f"{self.MODEL_ZH_EN} 模型加载完成")

        except Exception as e:
            logger.error(f"加载 {self.MODEL_ZH_EN} 模型失败: {e}")
            self.model_zh_en = None
            self.tokenizer_zh_en = None

    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        if not text or not text.strip():
            return "en"
        # 简单检测：如果有中文字符则为中文
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return "zh"
        return "en"

    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "zh-CN") -> str:
        """
        使用 MarianMT 模型进行离线翻译

        Args:
            text: 待翻译的文本
            source_lang: 源语言 ('auto', 'en', 'zh')
            target_lang: 目标语言 ('zh' for Chinese, 'en' for English)

        Returns:
            翻译后的文本
        """
        if not text or not text.strip():
            return text

        if not self.enabled:
            logger.warning("Translation service is disabled, returning original text")
            return text

        try:
            # 如果是自动检测，先检测语言
            if source_lang == "auto":
                source_lang = self._detect_language(text)

            # 简化语言代码
            sl = "zh" if source_lang.lower().startswith("zh") else "en"
            tl = "zh" if target_lang.lower().startswith("zh") else "en"

            # 英文 → 中文
            if sl == "en" and tl == "zh":
                self._load_model_en_zh()
                if self.model_en_zh is None:
                    logger.warning("英文→中文模型未加载，返回原文")
                    return text

                # Tokenize
                inputs = self.tokenizer_en_zh(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Generate
                with torch.no_grad():
                    outputs = self.model_en_zh.generate(**inputs, max_length=512)

                # Decode
                translated_text = self.tokenizer_en_zh.decode(outputs[0], skip_special_tokens=True)
                logger.info(f"Translated text from en to zh")
                return translated_text

            # 中文 → 英文
            elif sl == "zh" and tl == "en":
                self._load_model_zh_en()
                if self.model_zh_en is None:
                    logger.warning("中文→英文模型未加载，返回原文")
                    return text

                # Tokenize
                inputs = self.tokenizer_zh_en(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Generate
                with torch.no_grad():
                    outputs = self.model_zh_en.generate(**inputs, max_length=512)

                # Decode
                translated_text = self.tokenizer_zh_en.decode(outputs[0], skip_special_tokens=True)
                logger.info(f"Translated text from zh to en")
                return translated_text

            else:
                logger.warning(f"不支持的语言方向: {sl} → {tl}")
                return text

        except Exception as e:
            logger.error(f"Translation failed: {str(e)}", exc_info=True)
            return text

    def translate_segment(self, text: str, source_lang: str = "en") -> Dict[str, str]:
        """
        翻译文本片段并返回结构化结果

        Args:
            text: 待翻译的文本
            source_lang: 源语言 ('en', 'zh', 'auto')

        Returns:
            包含原文、译文和源语言的字典
        """
        result = {
            "zh": "",
            "en": "",
            "source_lang": source_lang
        }

        if not text or not text.strip():
            return result

        # 如果是自动检测，则先检测语言
        if source_lang == "auto":
            detected_lang = self._detect_language(text)
            result["source_lang"] = detected_lang
            source_lang = detected_lang

        try:
            # 根据源语言进行相应翻译
            if source_lang == "en":
                result["en"] = text
                result["zh"] = self.translate(text, source_lang="en", target_lang="zh")
            elif source_lang == "zh":
                result["zh"] = text
                result["en"] = self.translate(text, source_lang="zh", target_lang="en")
            else:
                # 默认当作英文处理
                result["en"] = text
                result["zh"] = self.translate(text, source_lang="auto", target_lang="zh")
        except Exception as e:
            logger.error(f"Segment translation failed: {str(e)}")
            # 失败时保存原文
            if source_lang == "en":
                result["en"] = text
                result["zh"] = text
            else:
                result["zh"] = text
                result["en"] = text

        return result

    def translate_all(self, segments: list) -> list:
        """
        翻译所有文本片段

        Args:
            segments: 文本片段列表，每个片段应包含 'text' 字段

        Returns:
            翻译后的片段列表
        """
        if not segments:
            return segments

        for segment in segments:
            text = segment.get("text", "")

            # 检测语言
            source_lang = self._detect_language(text)

            # 翻译该片段
            segment["translation"] = self.translate_segment(text, source_lang)

        return segments


translation_service = TranslationService()

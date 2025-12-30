import logging
from typing import Dict, Any
from deep_translator import GoogleTranslator
from app.core.config import TRANSLATION_ENABLED, DEEPL_API_KEY

logger = logging.getLogger(__name__)


class TranslationService:
    """翻译服务 - 使用 DeepL/Google Translator 实现中英文互译"""

    def __init__(self):
        self.enabled = TRANSLATION_ENABLED
        self.api_key = DEEPL_API_KEY

    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        if not text or not text.strip():
            return "en"
        # 简单检测：如果有中文字符则为中文
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return "zh"
        return "en"

    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "zh-cn") -> str:
        """
        使用 DeepL/Google Translator 进行翻译

        Args:
            text: 待翻译的文本
            source_lang: 源语言 ('auto', 'en', 'zh-CN', 'zh')
            target_lang: 目标语言 ('zh-CN' for Chinese, 'en' for English)

        Returns:
            翻译后的文本
        """
        if not text or not text.strip():
            return text

        if not self.enabled:
            logger.warning("Translation service is disabled, returning original text")
            return text

        try:
            # 使用 GoogleTranslator (免费, 无需API Key)
            # 注意: GoogleTranslator 使用 zh-CN (大写 CN)
            translator = GoogleTranslator(
                source=source_lang,
                target=target_lang
            )
            result = translator.translate(text)
            logger.info(f"Translated text from {source_lang} to {target_lang}")
            return result
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return text  # 翻译失败时返回原文

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
            # GoogleTranslator 使用 zh-CN (大写 CN)
            if source_lang == "en":
                result["en"] = text
                result["zh"] = self.translate(text, source_lang="en", target_lang="zh-CN")
            elif source_lang == "zh" or source_lang == "zh-CN" or source_lang == "zh-cn":
                result["zh"] = text
                result["en"] = self.translate(text, source_lang="zh-CN", target_lang="en")
            else:
                # 默认当作英文处理
                result["en"] = text
                result["zh"] = self.translate(text, source_lang="auto", target_lang="zh-CN")
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

#!/usr/bin/env python3
"""翻译功能测试脚本"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.translation_service import TranslationService

def test_translation():
    """测试翻译服务"""
    print("=" * 60)
    print("翻译功能测试")
    print("=" * 60)

    service = TranslationService()

    # 测试用例
    test_cases = [
        {
            "text": "Hello, how are you?",
            "source_lang": "en",
            "description": "英文翻译成中文"
        },
        {
            "text": "你好,你好吗?",
            "source_lang": "zh",
            "description": "中文翻译成英文"
        },
        {
            "text": "Today is a beautiful day.",
            "source_lang": "auto",
            "description": "自动检测语言并翻译"
        },
        {
            "text": "今天天气很好",
            "source_lang": "auto",
            "description": "自动检测中文并翻译"
        }
    ]

    # 测试单句翻译
    print("\n【单句翻译测试】\n")
    for i, test in enumerate(test_cases, 1):
        print(f"测试 {i}: {test['description']}")
        print(f"原文: {test['text']}")
        result = service.translate_segment(test['text'], test['source_lang'])
        print(f"译文: {result}")
        print("-" * 60)

    # 测试批量翻译
    print("\n【批量翻译测试】\n")
    segments = [
        {"text": "This is the first sentence.", "start": 0.0, "end": 2.5},
        {"text": "这是第二句话。", "start": 2.5, "end": 5.0},
        {"text": "The third sentence is here.", "start": 5.0, "end": 7.5},
    ]

    print("原始片段:")
    for seg in segments:
        print(f"  - {seg['text']}")

    translated = service.translate_all(segments)
    print("\n翻译后片段:")
    for seg in translated:
        trans = seg.get("translation", {})
        print(f"  - 原文: {seg['text']}")
        print(f"    译文: {trans}")
        print()

    # 测试空文本
    print("\n【边界情况测试】\n")
    print("空文本测试:")
    result = service.translate_segment("", "en")
    print(f"  结果: {result}")

    print("\n仅空格文本测试:")
    result = service.translate_segment("   ", "en")
    print(f"  结果: {result}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_translation()

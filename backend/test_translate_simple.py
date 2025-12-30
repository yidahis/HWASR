#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from app.services.translation_service import TranslationService

service = TranslationService()

print('=== 英译中 ===')
result = service.translate_segment('Hello, how are you today?', 'en')
print(f'原文: Hello, how are you today?')
print(f'译文: {result}')
print()

print('=== 中译英 ===')
result = service.translate_segment('你好,今天天气怎么样?', 'zh')
print(f'原文: 你好,今天天气怎么样?')
print(f'译文: {result}')

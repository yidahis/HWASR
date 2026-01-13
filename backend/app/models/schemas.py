from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TranslationModel(BaseModel):
    zh: str
    en: str
    source_lang: str


class SentenceSegment(BaseModel):
    text: str
    start: float
    end: float
    speaker: int
    translation: TranslationModel


class ASRResult(BaseModel):
    success: bool
    result_id: str
    text: str
    sentences: List[SentenceSegment]
    speakers: List[int]
    total_duration: float
    audio_hash: str
    filename: str
    timestamp: str
    message: str
    audio_path: str
    updated_timestamp: Optional[str] = None
    processing_time: Optional[float] = None  # 处理耗时（秒）


class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float
    message: str
    result_id: Optional[str] = None

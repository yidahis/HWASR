export interface TranslationModel {
  zh: string
  en: string
  source_lang: string
}

export interface SentenceSegment {
  text: string
  start: number
  end: number
  speaker: number
  translation: TranslationModel
}

export interface ASRResult {
  success: boolean
  result_id: string
  text: string
  sentences: SentenceSegment[]
  speakers: number[]
  total_duration: number
  audio_hash: string
  filename: string
  timestamp: string
  message: string
  audio_path: string
  updated_timestamp?: string
  processing_time?: number  // 处理耗时（秒）
}

export interface TaskStatus {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message: string
  result_id?: string
}

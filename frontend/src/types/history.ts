export interface HistoryItem {
  result_id: string
  filename: string
  timestamp: string
  total_duration: number
  speaker_count: number
  text_preview: string
}

export interface HistoryDetail extends HistoryItem {
  sentences: any[]
  speakers: number[]
  audio_hash: string
  audio_path: string
  message: string
  success: boolean
  updated_timestamp?: string
}

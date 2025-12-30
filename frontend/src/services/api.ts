import axios from 'axios'
import type { TaskStatus, ASRResult } from '@/types/api'

const API_BASE_URL = 'http://localhost:8002/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const uploadAudio = async (
  file: File,
  onProgress?: (progress: number) => void
): Promise<TaskStatus> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<TaskStatus>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total) {
        const progress = (progressEvent.loaded / progressEvent.total) * 100
        onProgress?.(progress)
      }
    },
  })
  return response.data
}

export const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  const response = await api.get<TaskStatus>(`/status/${taskId}`)
  return response.data
}

export const getResult = async (resultId: string): Promise<ASRResult> => {
  const response = await api.get<ASRResult>(`/result/${resultId}`)
  return response.data
}

export const getAudioUrl = (resultId: string): string => {
  return `${API_BASE_URL}/audio/${resultId}`
}

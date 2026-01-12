import axios from 'axios'
import type { TaskStatus, ASRResult } from '@/types/api'

const API_BASE_URL = 'http://localhost:8003/api'

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

export const importResult = async (
  jsonFile: File,
  audioFile: File
): Promise<{ success: boolean; message: string; result_id: string }> => {
  const formData = new FormData()
  formData.append('json_file', jsonFile)
  formData.append('audio_file', audioFile)

  const response = await api.post('/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const downloadAudioFromUrl = async (
  url: string
): Promise<TaskStatus> => {
  const response = await api.post<TaskStatus>('/download-url', null, {
    params: { url }
  })
  return response.data
}

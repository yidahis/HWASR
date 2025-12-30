import { api } from './api'
import type { HistoryItem, HistoryDetail } from '@/types/history'

export const getHistoryList = async (): Promise<HistoryItem[]> => {
  const response = await api.get<HistoryItem[]>('/history/list')
  return response.data
}

export const loadHistory = async (resultId: string): Promise<HistoryDetail> => {
  const response = await api.get<HistoryDetail>(`/history/load/${resultId}`)
  return response.data
}

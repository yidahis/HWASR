import { useState, useEffect } from 'react'
import { Clock, Mic, Users, X, Loader2 } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent } from './ui/card'
import { ScrollArea } from './ui/scroll-area'
import { getHistoryList, loadHistory } from '@/services/historyApi'
import type { HistoryItem } from '@/types/history'
import { formatDuration } from '@/lib/utils'

interface HistoryModalProps {
  isOpen: boolean
  onClose: () => void
  onLoadHistory: (history: any) => void
}

export const HistoryModal = ({ isOpen, onClose, onLoadHistory }: HistoryModalProps) => {
  const [historyList, setHistoryList] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingDetail, setLoadingDetail] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      fetchHistoryList()
    }
  }, [isOpen])

  const fetchHistoryList = async () => {
    setLoading(true)
    try {
      const list = await getHistoryList()
      setHistoryList(list)
    } catch (error) {
      console.error('获取历史记录失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLoadHistory = async (item: HistoryItem) => {
    setLoadingDetail(item.result_id)
    try {
      const detail = await loadHistory(item.result_id)
      onLoadHistory(detail)
      onClose()
    } catch (error) {
      console.error('加载历史记录失败:', error)
      alert('加载失败，请重试')
    } finally {
      setLoadingDetail(null)
    }
  }

  const formatDate = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return timestamp
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 背景遮罩 */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* 模态框内容 */}
      <Card className="relative w-full max-w-2xl bg-slate-900/95 border border-slate-700/50 shadow-2xl">
        <CardContent className="p-6">
          {/* 标题栏 */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-br from-primary to-accent rounded-lg">
                <Clock className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">历史记录</h2>
                <p className="text-sm text-slate-400">
                  {historyList.length > 0 ? `共 ${historyList.length} 条记录` : '暂无记录'}
                </p>
              </div>
            </div>
            <Button
              onClick={onClose}
              variant="ghost"
              size="sm"
              className="text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          {/* 列表内容 */}
          <div className="min-h-[300px] max-h-[500px]">
            {loading ? (
              <div className="flex items-center justify-center h-[300px]">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
              </div>
            ) : historyList.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[300px] text-center">
                <Clock className="w-16 h-16 text-slate-600 mb-4" />
                <p className="text-slate-400">暂无历史记录</p>
                <p className="text-sm text-slate-500 mt-1">上传音频文件开始识别后，记录将显示在这里</p>
              </div>
            ) : (
              <ScrollArea className="h-[500px]">
                <div className="space-y-3 pr-4">
                  {historyList.map((item, index) => (
                    <div
                      key={index}
                      className="p-4 bg-slate-800/50 hover:bg-slate-800 rounded-lg border border-slate-700/50 transition-all group"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          {/* 文件名 */}
                          <div className="flex items-center space-x-2 mb-2">
                            <Mic className="w-4 h-4 text-primary flex-shrink-0" />
                            <h3 className="text-sm font-medium text-white truncate">
                              {item.filename || `记录 #${item.result_id.slice(0, 8)}`}
                            </h3>
                          </div>

                          {/* 元数据 */}
                          <div className="flex items-center flex-wrap gap-3 text-xs text-slate-400">
                            <div className="flex items-center space-x-1">
                              <Clock className="w-3 h-3" />
                              <span>{formatDate(item.timestamp)}</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <Users className="w-3 h-3" />
                              <span>{item.speaker_count} 人说话</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <span className="w-2 h-2 bg-slate-600 rounded-full" />
                              <span>{formatDuration(item.total_duration)}</span>
                            </div>
                          </div>

                          {/* 文本预览 */}
                          <p className="mt-2 text-xs text-slate-500 line-clamp-2">
                            {item.text_preview}
                          </p>
                        </div>

                        {/* 加载按钮 */}
                        <Button
                          onClick={() => handleLoadHistory(item)}
                          disabled={loadingDetail === item.result_id}
                          variant="default"
                          size="sm"
                          className="flex-shrink-0"
                        >
                          {loadingDetail === item.result_id ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              加载中
                            </>
                          ) : (
                            '加载'
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

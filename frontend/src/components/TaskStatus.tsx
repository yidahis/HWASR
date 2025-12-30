import { useEffect, useState } from 'react'
import { Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Card, CardContent } from './ui/card'
import { Progress } from './ui/progress'
import { getTaskStatus, type TaskStatus } from '@/services/api'

interface TaskStatusComponentProps {
  taskId: string
  onComplete: (resultId: string) => void
  onError: (message: string) => void
}

export const TaskStatusComponent = ({ taskId, onComplete, onError }: TaskStatusComponentProps) => {
  const [status, setStatus] = useState<TaskStatus | null>(null)

  useEffect(() => {
    const pollInterval = setInterval(async () => {
      try {
        const result = await getTaskStatus(taskId)
        setStatus(result)
        
        if (result.status === 'completed' && result.result_id) {
          clearInterval(pollInterval)
          onComplete(result.result_id)
        } else if (result.status === 'failed') {
          clearInterval(pollInterval)
          onError(result.message)
        }
      } catch (error) {
        console.error('Failed to fetch task status:', error)
      }
    }, 2000)

    return () => clearInterval(pollInterval)
  }, [taskId, onComplete, onError])

  if (!status) {
    return (
      <Card>
        <CardContent className="p-6 flex items-center justify-center space-x-3">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
          <p className="text-slate-300">正在获取任务状态...</p>
        </CardContent>
      </Card>
    )
  }

  const getStatusIcon = () => {
    switch (status.status) {
      case 'pending':
        return <Clock className="w-6 h-6 text-slate-400" />
      case 'processing':
        return <Loader2 className="w-6 h-6 animate-spin text-primary" />
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />
      case 'failed':
        return <XCircle className="w-6 h-6 text-red-500" />
    }
  }

  const getStatusText = () => {
    switch (status.status) {
      case 'pending':
        return '等待处理'
      case 'processing':
        return '正在处理'
      case 'completed':
        return '识别完成'
      case 'failed':
        return '处理失败'
    }
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            {getStatusIcon()}
            <div className="flex-1">
              <p className="font-semibold text-white text-lg">{getStatusText()}</p>
              <p className="text-sm text-slate-400">{status.message}</p>
            </div>
            {status.progress > 0 && (
              <span className="text-2xl font-bold text-primary">
                {status.progress.toFixed(0)}%
              </span>
            )}
          </div>

          {status.status === 'processing' && (
            <div>
              <Progress value={status.progress} />
            </div>
          )}

          {status.status === 'failed' && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <p className="text-red-400 font-medium">处理失败</p>
              <p className="text-red-300 text-sm mt-1">{status.message}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

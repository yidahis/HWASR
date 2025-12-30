import { useState } from 'react'
import { Mic, RefreshCw } from 'lucide-react'
import { AudioUploader } from './components/AudioUploader'
import { TaskStatusComponent } from './components/TaskStatus'
import { ResultViewer } from './components/ResultViewer'
import { uploadAudio, getResult, type ASRResult } from './services/api'

type AppState = 'upload' | 'processing' | 'result'

function App() {
  const [appState, setAppState] = useState<AppState>('upload')
  const [taskId, setTaskId] = useState<string>('')
  const [result, setResult] = useState<ASRResult | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  const handleUpload = async (file: File) => {
    setIsUploading(true)
    setUploadProgress(0)

    try {
      const response = await uploadAudio(file, (progress) => {
        setUploadProgress(progress)
      })
      setTaskId(response.task_id)
      setAppState('processing')
    } catch (error) {
      console.error('Upload failed:', error)
      alert('上传失败，请重试')
    } finally {
      setIsUploading(false)
    }
  }

  const handleTaskComplete = async (resultId: string) => {
    try {
      const resultData = await getResult(resultId)
      setResult(resultData)
      setAppState('result')
    } catch (error) {
      console.error('Failed to get result:', error)
      alert('获取结果失败，请重试')
    }
  }

  const handleTaskError = (message: string) => {
    alert(`处理失败: ${message}`)
    setAppState('upload')
  }

  const handleReset = () => {
    setAppState('upload')
    setTaskId('')
    setResult(null)
    setIsUploading(false)
    setUploadProgress(0)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <header className="fixed top-0 left-0 right-0 z-50 glass-dark border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-br from-primary to-accent rounded-lg">
                <Mic className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Whisper ASR</h1>
                <p className="text-sm text-slate-400">智能语音识别系统</p>
              </div>
            </div>

            {appState !== 'upload' && (
              <button
                onClick={handleReset}
                className="flex items-center space-x-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4 text-slate-300" />
                <span className="text-sm text-white">新建任务</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="pt-24 pb-12 px-6">
        <div className="max-w-7xl mx-auto">
          {appState === 'upload' && (
            <div className="space-y-8">
              <div className="text-center">
                <h2 className="text-4xl font-bold text-white mb-4">
                  上传音频文件开始识别
                </h2>
                <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                  使用 Whisper-large-v3-turbo 模型进行高精度语音识别，
                  支持自动说话人分离和多语言翻译
                </p>
              </div>

              <AudioUploader
                onUpload={handleUpload}
                isUploading={isUploading}
                uploadProgress={uploadProgress}
              />
            </div>
          )}

          {appState === 'processing' && taskId && (
            <div className="max-w-2xl mx-auto space-y-8">
              <div className="text-center">
                <h2 className="text-4xl font-bold text-white mb-4">
                  正在处理您的音频
                </h2>
                <p className="text-lg text-slate-400">
                  请稍候，系统正在进行语音识别和说话人分离
                </p>
              </div>

              <TaskStatusComponent
                taskId={taskId}
                onComplete={handleTaskComplete}
                onError={handleTaskError}
              />
            </div>
          )}

          {appState === 'result' && result && (
            <ResultViewer result={result} />
          )}
        </div>
      </main>

      <footer className="fixed bottom-0 left-0 right-0 glass-dark border-t border-slate-700/50 py-4">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-sm text-slate-400">
            基于 Whisper-large-v3-turbo 和 WhisperX 构建 | 本地部署，数据隐私安全
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App

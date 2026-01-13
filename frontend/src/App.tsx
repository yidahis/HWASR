import { useState } from 'react'
import { Mic, RefreshCw, Clock, Upload, Link } from 'lucide-react'
import { AudioUploader } from './components/AudioUploader'
import { TaskStatusComponent } from './components/TaskStatus'
import { ResultViewer } from './components/ResultViewer'
import { HistoryModal } from './components/HistoryModal'
import { ImportData } from './components/ImportData'
import { uploadAudio, getResult, downloadAudioFromUrl } from './services/api'
import type { ASRResult } from './types/api'

type AppState = 'upload' | 'processing' | 'result'
type UploadMethod = 'file' | 'url'

function App() {
  const [appState, setAppState] = useState<AppState>('upload')
  const [taskId, setTaskId] = useState<string>('')
  const [result, setResult] = useState<ASRResult | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false)
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [uploadMethod, setUploadMethod] = useState<UploadMethod>('file')
  const [audioUrl, setAudioUrl] = useState('')
  const [isDownloading, setIsDownloading] = useState(false)

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

  const handleDownloadFromUrl = async () => {
    if (!audioUrl.trim()) {
      alert('请输入音频链接')
      return
    }

    setIsDownloading(true)

    try {
      const response = await downloadAudioFromUrl(audioUrl.trim())
      setTaskId(response.task_id)
      setAppState('processing')
      setAudioUrl('')
    } catch (error: any) {
      console.error('Download failed:', error)
      alert(error.message || '下载失败，请重试')
    } finally {
      setIsDownloading(false)
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

  const handleLoadHistory = (history: ASRResult) => {
    setResult(history)
    setAppState('result')
  }

  const handleResultUpdate = (updatedResult: ASRResult) => {
    setResult(updatedResult)
  }

  const handleImportSuccess = async (resultId: string) => {
    try {
      const resultData = await getResult(resultId)
      setResult(resultData)
      setAppState('result')
      setIsImportModalOpen(false)
    } catch (error) {
      console.error('Failed to get imported result:', error)
      alert('获取导入结果失败，请重试')
    }
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

            <div className="flex items-center space-x-3">
              <button
                onClick={() => setIsHistoryModalOpen(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
              >
                <Clock className="w-4 h-4 text-slate-300" />
                <span className="text-sm text-white">历史记录</span>
              </button>

              <button
                onClick={() => setIsImportModalOpen(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
              >
                <Upload className="w-4 h-4 text-slate-300" />
                <span className="text-sm text-white">导入</span>
              </button>

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

              {/* 文件上传方式 */}
              {uploadMethod === 'file' && (
                <AudioUploader
                  onUpload={handleUpload}
                  isUploading={isUploading}
                  uploadProgress={uploadProgress}
                />
              )}

              {/* 链接下载方式 */}
              {uploadMethod === 'url' && (
                <div className="max-w-2xl mx-auto">
                  <div className="glass-dark rounded-xl p-8 border border-slate-700/50">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          音频链接
                        </label>
                        <input
                          type="url"
                          value={audioUrl}
                          onChange={(e) => setAudioUrl(e.target.value)}
                          placeholder="请输入音频文件的 URL 链接"
                          className="w-full px-4 py-3 bg-white/5 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50"
                          disabled={isDownloading}
                        />
                      </div>
                      <button
                        onClick={handleDownloadFromUrl}
                        disabled={isDownloading || !audioUrl.trim()}
                        className={`w-full py-3 rounded-lg font-medium transition-all ${
                          isDownloading || !audioUrl.trim()
                            ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                            : 'bg-gradient-to-r from-primary to-accent text-white hover:opacity-90'
                        }`}
                      >
                        {isDownloading ? '下载中...' : '下载并识别'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
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
            <ResultViewer result={result} onResultUpdate={handleResultUpdate} />
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

      {/* 历史记录模态框 */}
      <HistoryModal
        isOpen={isHistoryModalOpen}
        onClose={() => setIsHistoryModalOpen(false)}
        onLoadHistory={handleLoadHistory}
      />

      {/* 导入数据模态框 */}
      {isImportModalOpen && (
        <ImportData
          onImportSuccess={handleImportSuccess}
          onCancel={() => setIsImportModalOpen(false)}
        />
      )}
    </div>
  )
}

export default App

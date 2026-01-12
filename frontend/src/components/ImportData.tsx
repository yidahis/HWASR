import { useState, useRef } from 'react'
import { Upload, FileJson, FileAudio, X, Loader2 } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent } from './ui/card'
import { Progress } from './ui/progress'
import { importResult } from '@/services/api'

interface ImportDataProps {
  onImportSuccess: (resultId: string) => void
  onCancel: () => void
}

export const ImportData = ({ onImportSuccess, onCancel }: ImportDataProps) => {
  const [jsonFile, setJsonFile] = useState<File | null>(null)
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [isImporting, setIsImporting] = useState(false)
  const [importProgress, setImportProgress] = useState(0)
  const jsonInputRef = useRef<HTMLInputElement>(null)
  const audioInputRef = useRef<HTMLInputElement>(null)

  const handleJsonSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setJsonFile(file)
    }
  }

  const handleAudioSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setAudioFile(file)
    }
  }

  const handleRemoveJson = () => {
    setJsonFile(null)
    if (jsonInputRef.current) {
      jsonInputRef.current.value = ''
    }
  }

  const handleRemoveAudio = () => {
    setAudioFile(null)
    if (audioInputRef.current) {
      audioInputRef.current.value = ''
    }
  }

  const handleImport = async () => {
    if (!jsonFile || !audioFile) {
      alert('请同时选择 JSON 文件和音频文件')
      return
    }

    setIsImporting(true)
    setImportProgress(0)

    try {
      // 模拟进度
      const progressInterval = setInterval(() => {
        setImportProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      const result = await importResult(jsonFile, audioFile)

      clearInterval(progressInterval)
      setImportProgress(100)

      if (result.success) {
        setTimeout(() => {
          onImportSuccess(result.result_id)
        }, 500)
      } else {
        alert('导入失败: ' + result.message)
        setIsImporting(false)
        setImportProgress(0)
      }
    } catch (error) {
      console.error('导入失败:', error)
      alert('导入失败，请重试')
      setIsImporting(false)
      setImportProgress(0)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl bg-slate-900 border-slate-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">导入数据</h2>
            <button
              onClick={onCancel}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
              disabled={isImporting}
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>

          <div className="space-y-6">
            {/* JSON 文件选择 */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                JSON 结果文件
              </label>
              {!jsonFile ? (
                <div
                  onClick={() => jsonInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center cursor-pointer hover:border-slate-500 transition-colors"
                >
                  <FileJson className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                  <p className="text-sm text-slate-400 mb-2">
                    点击选择 JSON 文件
                  </p>
                  <p className="text-xs text-slate-500">
                    支持之前导出的 JSON 格式
                  </p>
                  <input
                    ref={jsonInputRef}
                    type="file"
                    accept=".json"
                    onChange={handleJsonSelect}
                    className="hidden"
                  />
                </div>
              ) : (
                <div className="flex items-center justify-between p-4 bg-slate-800 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <FileJson className="w-8 h-8 text-green-500" />
                    <div>
                      <p className="text-sm text-white font-medium">
                        {jsonFile.name}
                      </p>
                      <p className="text-xs text-slate-400">
                        {(jsonFile.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleRemoveJson}
                    disabled={isImporting}
                    className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4 text-slate-400" />
                  </button>
                </div>
              )}
            </div>

            {/* 音频文件选择 */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                对应的音频文件
              </label>
              {!audioFile ? (
                <div
                  onClick={() => audioInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center cursor-pointer hover:border-slate-500 transition-colors"
                >
                  <FileAudio className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                  <p className="text-sm text-slate-400 mb-2">
                    点击选择音频文件
                  </p>
                  <p className="text-xs text-slate-500">
                    支持 WAV, MP3, M4A 等格式
                  </p>
                  <input
                    ref={audioInputRef}
                    type="file"
                    accept="audio/*"
                    onChange={handleAudioSelect}
                    className="hidden"
                  />
                </div>
              ) : (
                <div className="flex items-center justify-between p-4 bg-slate-800 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <FileAudio className="w-8 h-8 text-green-500" />
                    <div>
                      <p className="text-sm text-white font-medium">
                        {audioFile.name}
                      </p>
                      <p className="text-xs text-slate-400">
                        {(audioFile.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleRemoveAudio}
                    disabled={isImporting}
                    className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4 text-slate-400" />
                  </button>
                </div>
              )}
            </div>

            {/* 导入进度 */}
            {isImporting && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">正在导入...</span>
                  <span className="text-white font-medium">
                    {importProgress.toFixed(0)}%
                  </span>
                </div>
                <Progress value={importProgress} />
              </div>
            )}

            {/* 操作按钮 */}
            <div className="flex items-center space-x-3">
              <Button
                onClick={handleImport}
                disabled={!jsonFile || !audioFile || isImporting}
                className="flex-1"
              >
                {isImporting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    导入中...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    开始导入
                  </>
                )}
              </Button>
              <Button
                onClick={onCancel}
                disabled={isImporting}
                variant="outline"
              >
                取消
              </Button>
            </div>

            <p className="text-xs text-slate-500 text-center">
              导入后将创建新的结果记录，您可以继续编辑和查看
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

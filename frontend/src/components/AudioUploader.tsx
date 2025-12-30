import { useState, useRef } from 'react'
import { Upload, FileAudio, X } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent } from './ui/card'
import { Progress } from './ui/progress'

interface AudioUploaderProps {
  onUpload: (file: File) => void
  isUploading: boolean
  uploadProgress: number
}

export const AudioUploader = ({ onUpload, isUploading, uploadProgress }: AudioUploaderProps) => {
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (file: File) => {
    const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/mp4', 'audio/x-m4a', 'audio/flac']
    if (!validTypes.includes(file.type)) {
      alert('请上传有效的音频文件 (WAV, MP3, M4A, FLAC)')
      return
    }
    
    if (file.size > 500 * 1024 * 1024) {
      alert('文件大小不能超过 500MB')
      return
    }

    setSelectedFile(file)
  }

  const handleUpload = () => {
    if (selectedFile) {
      onUpload(selectedFile)
    }
  }

  const clearFile = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <Card className="w-full">
      <CardContent className="pt-6">
        <div
          className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
            dragActive
              ? 'border-primary bg-primary/10'
              : 'border-slate-600 hover:border-primary/50 hover:bg-white/5'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            onChange={handleChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={isUploading}
          />
          
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className={`p-4 rounded-full transition-colors ${
              dragActive ? 'bg-primary' : 'bg-slate-700'
            }`}>
              <FileAudio className="w-12 h-12 text-white" />
            </div>
            
            <div>
              <p className="text-lg font-medium text-white mb-2">
                拖拽音频文件到此处或点击上传
              </p>
              <p className="text-sm text-slate-400">
                支持 WAV, MP3, M4A, FLAC 格式，最大 500MB
              </p>
            </div>

            <Button
              onClick={(e) => {
                e.stopPropagation()
                fileInputRef.current?.click()
              }}
              variant="outline"
              disabled={isUploading}
            >
              <Upload className="w-4 h-4 mr-2" />
              选择文件
            </Button>
          </div>

          {selectedFile && (
            <div className="mt-6 p-4 glass-dark rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <FileAudio className="w-8 h-8 text-primary" />
                  <div>
                    <p className="font-medium text-white">{selectedFile.name}</p>
                    <p className="text-sm text-slate-400">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={clearFile}
                  disabled={isUploading}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>

              {isUploading ? (
                <div className="mt-4">
                  <Progress value={uploadProgress} />
                  <p className="text-sm text-slate-400 mt-2">
                    正在上传... {uploadProgress.toFixed(0)}%
                  </p>
                </div>
              ) : (
                <Button
                  onClick={handleUpload}
                  className="w-full mt-4"
                  disabled={!selectedFile}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  开始识别
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

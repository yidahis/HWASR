import { useState, useEffect, useRef } from 'react'
import { Play, Pause, Download, Mic, Zap } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { ScrollArea } from './ui/scroll-area'
import { SentenceItem } from './SentenceItem'
import { useAudioPlayer } from '@/hooks/useAudioPlayer'
import { getAudioUrl, api } from '@/services/api'
import type { ASRResult, SentenceSegment } from '@/types/api'
import { formatDuration } from '@/lib/utils'

interface ResultViewerProps {
  result: ASRResult
  onResultUpdate?: (updatedResult: ASRResult) => void
}

export const ResultViewer = ({ result, onResultUpdate }: ResultViewerProps) => {
  const { audioRef, isPlaying, currentTime, duration, toggle, playRange, isReady } = useAudioPlayer()
  const [activeSegmentId, setActiveSegmentId] = useState<number | null>(null)
  const [sentences, setSentences] = useState<SentenceSegment[]>(result.sentences)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const segmentRefs = useRef<Map<number, HTMLDivElement>>(new Map())
  const audioUrl = getAudioUrl(result.result_id)

  // 当 result prop 更新时，同步更新 sentences 状态
  useEffect(() => {
    setSentences(result.sentences)
  }, [result.sentences])

  useEffect(() => {
    const currentSegment = sentences.find(
      (seg) => currentTime >= seg.start && currentTime <= seg.end
    )
    if (currentSegment) {
      setActiveSegmentId(sentences.indexOf(currentSegment))
    }
  }, [currentTime, sentences])

  useEffect(() => {
    if (activeSegmentId !== null) {
      const element = segmentRefs.current.get(activeSegmentId)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }
  }, [activeSegmentId])

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.load()
    }
  }, [audioUrl, audioRef])

  const handleSegmentClick = (segment: SentenceSegment) => {
    console.log('Segment clicked:', segment, 'isReady:', isReady)
    if (!isReady) {
      console.log('Audio not ready yet, waiting...')
      return
    }
    playRange(segment.start, segment.end)
  }

  const handleDownload = async () => {
    const response = await fetch(`http://localhost:8003/api/download/${result.result_id}`)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${result.result_id}_result.zip`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getSpeakerCount = () => {
    const uniqueSpeakers = [...new Set(sentences.map(s => s.speaker))]
    return uniqueSpeakers.length
  }

  const formatProcessingTime = (seconds?: number) => {
    if (!seconds) return '-'
    if (seconds < 60) {
      return `${seconds.toFixed(1)}秒`
    }
    const minutes = Math.floor(seconds / 60)
    const secs = (seconds % 60).toFixed(1)
    return `${minutes}分${secs}秒`
  }

  const handleMerge = async (index: number) => {
    if (index > 0) {
      const newSentences = [...sentences]
      // 合并文本
      const currentText = newSentences[index].text
      const prevText = newSentences[index - 1].text
      const mergedText = prevText + ' ' + currentText

      // 更新上一句的文本和结束时间
      newSentences[index - 1].text = mergedText
      newSentences[index - 1].end = newSentences[index].end

      // 删除当前句
      newSentences.splice(index, 1)

      // 更新活跃索引
      const newActiveId = activeSegmentId !== null && activeSegmentId > index
        ? activeSegmentId - 1
        : activeSegmentId

      setSentences(newSentences)
      setActiveSegmentId(newActiveId)

      // 保存到后端 JSON 文件
      try {
        const response = await api.post(`/update/${result.result_id}`, { sentences: newSentences })
        console.log('保存合并结果成功:', response.data)

        // 从后端重新加载数据确保同步
        const reloadResponse = await api.get(`/result/${result.result_id}`)
        if (onResultUpdate) {
          onResultUpdate(reloadResponse.data)
        }
      } catch (error) {
        console.error('保存合并结果失败:', error)
        alert('保存失败，请重试')
      }
    }
  }

  const handleUpdateSentence = async (index: number, newText: string) => {
    const newSentences = [...sentences]
    newSentences[index].text = newText
    setSentences(newSentences)

    // 保存到后端 JSON 文件
    try {
      const response = await api.post(`/update/${result.result_id}`, { sentences: newSentences })
      console.log('保存编辑结果成功:', response.data)

      // 从后端重新加载数据确保同步
      const reloadResponse = await api.get(`/result/${result.result_id}`)
      if (onResultUpdate) {
        onResultUpdate(reloadResponse.data)
      }
    } catch (error) {
      console.error('保存编辑结果失败:', error)
      alert('保存失败，请重试')
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CardTitle className="text-2xl">识别结果</CardTitle>
              {result.processing_time && (
                <div className="flex items-center space-x-1.5 text-sm text-slate-400" style={{ fontSize: '14px' }}>
                  <Zap className="w-4 h-4 text-yellow-400" />
                  <span>{formatProcessingTime(result.processing_time)}</span>
                  {result.total_duration > 0 && result.processing_time > 0 && (
                    <span className="text-primary font-medium">
                      ({(result.total_duration / result.processing_time).toFixed(2)}x)
                    </span>
                  )}
                </div>
              )}
            </div>
            <Button onClick={handleDownload} variant="outline">
              <Download className="w-4 h-4 mr-2" />
              导出 JSON+音频
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="p-4 glass-dark rounded-lg">
              <p className="text-sm text-slate-400 mb-1">总时长</p>
              <p className="text-2xl font-bold text-white">
                {formatDuration(result.total_duration)}
              </p>
            </div>
            <div className="p-4 glass-dark rounded-lg">
              <p className="text-sm text-slate-400 mb-1">句子数量</p>
              <p className="text-2xl font-bold text-white">
                {sentences.length}
              </p>
            </div>
            <div className="p-4 glass-dark rounded-lg">
              <p className="text-sm text-slate-400 mb-1">说话人数</p>
              <p className="text-2xl font-bold text-white">
                {getSpeakerCount()}
              </p>
            </div>
            <div className="p-4 glass-dark rounded-lg">
              <p className="text-sm text-slate-400 mb-1">识别语言</p>
              <p className="text-2xl font-bold text-white">
                {sentences[0]?.translation?.source_lang?.toUpperCase() || 'AUTO'}
              </p>
            </div>
          </div>

          <div className="p-4 glass-dark rounded-lg mb-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Mic className="w-5 h-5 text-primary" />
                <span className="font-medium text-white">音频播放器</span>
              </div>
              <Button onClick={toggle} variant="default">
                {isPlaying ? (
                  <Pause className="w-4 h-4" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
              </Button>
            </div>

            <audio ref={audioRef} src={audioUrl} preload="auto" className="w-full" />

            <div className="mt-3 flex items-center space-x-3 text-sm">
              <span className="text-slate-400">
                {duration > 0 ? formatDuration(currentTime) : '0:00'}
              </span>
              <div className="flex-1 h-1 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary to-accent"
                  style={{
                    width: duration > 0 ? `${(currentTime / duration) * 100}%` : '0%'
                  }}
                />
              </div>
              <span className="text-slate-400">
                {formatDuration(duration)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <h3 className="text-xl font-bold text-white mb-4">转录内容</h3>
          <ScrollArea className="h-[600px] pr-2" ref={scrollAreaRef}>
            <div className="space-y-3">
              {sentences.map((segment, index) => (
                <div
                  key={index}
                  ref={(el) => {
                    if (el) {
                      segmentRefs.current.set(index, el)
                    } else {
                      segmentRefs.current.delete(index)
                    }
                  }}
                  className="relative"
                >
                  <SentenceItem
                    segment={segment}
                    isActive={activeSegmentId === index}
                    onClick={() => handleSegmentClick(segment)}
                    index={index}
                    onMerge={() => handleMerge(index)}
                    onUpdate={(text) => handleUpdateSentence(index, text)}
                  />
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

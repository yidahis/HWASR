import { useState, useEffect, useRef } from 'react'
import { Play, Pause, Download, Mic } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { ScrollArea } from './ui/scroll-area'
import { SentenceItem } from './SentenceItem'
import { useAudioPlayer } from '@/hooks/useAudioPlayer'
import { getAudioUrl } from '@/services/api'
import type { ASRResult, SentenceSegment } from '@/types/api'
import { formatDuration } from '@/lib/utils'

interface ResultViewerProps {
  result: ASRResult
}

export const ResultViewer = ({ result }: ResultViewerProps) => {
  const { audioRef, isPlaying, currentTime, duration, toggle, playRange, isReady } = useAudioPlayer()
  const [activeSegmentId, setActiveSegmentId] = useState<number | null>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const segmentRefs = useRef<Map<number, HTMLDivElement>>(new Map())
  const audioUrl = getAudioUrl(result.result_id)

  useEffect(() => {
    const currentSegment = result.sentences.find(
      (seg) => currentTime >= seg.start && currentTime <= seg.end
    )
    if (currentSegment) {
      setActiveSegmentId(result.sentences.indexOf(currentSegment))
    }
  }, [currentTime, result.sentences])

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
    const response = await fetch(`/api/download/${result.result_id}`)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${result.result_id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getSpeakerCount = () => {
    const uniqueSpeakers = [...new Set(result.sentences.map(s => s.speaker))]
    return uniqueSpeakers.length
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl">识别结果</CardTitle>
            <Button onClick={handleDownload} variant="outline">
              <Download className="w-4 h-4 mr-2" />
              导出 JSON
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
                {result.sentences.length}
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
                {result.sentences[0]?.translation.source_lang?.toUpperCase() || 'AUTO'}
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

            <audio ref={audioRef} src={audioUrl} className="w-full" />

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
              {result.sentences.map((segment, index) => (
                <div
                  key={index}
                  ref={(el) => {
                    if (el) {
                      segmentRefs.current.set(index, el)
                    } else {
                      segmentRefs.current.delete(index)
                    }
                  }}
                >
                  <SentenceItem
                    segment={segment}
                    isActive={activeSegmentId === index}
                    onClick={() => handleSegmentClick(segment)}
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

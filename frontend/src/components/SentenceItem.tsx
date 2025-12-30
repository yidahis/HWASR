import { CheckCircle, Volume2 } from 'lucide-react'
import { cn, formatTimestamp } from '@/lib/utils'
import type { SentenceSegment } from '@/types/api'

interface SentenceItemProps {
  segment: SentenceSegment
  isActive: boolean
  onClick: () => void
}

export const SentenceItem = ({ segment, isActive, onClick }: SentenceItemProps) => {
  return (
    <div
      onClick={onClick}
      className={cn(
        "p-4 rounded-lg border transition-all duration-200 cursor-pointer hover:bg-white/5",
        isActive
          ? "bg-primary/20 border-primary"
          : "bg-slate-800/50 border-slate-700/50"
      )}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-3">
          <div
            className={cn(
              "px-2 py-1 rounded-md text-xs font-bold",
              isActive ? "bg-primary text-white" : "bg-slate-700 text-slate-300"
            )}
          >
            SPEAKER_{segment.speaker.toString().padStart(2, '0')}
          </div>
          <span
            className={cn(
              "text-sm font-mono",
              isActive ? "text-primary" : "text-slate-400"
            )}
          >
            {formatTimestamp(segment.start)} - {formatTimestamp(segment.end)}
          </span>
        </div>
        {isActive && (
          <CheckCircle className="w-5 h-5 text-primary" />
        )}
      </div>

      <p
        className={cn(
          "text-sm leading-relaxed",
          isActive ? "text-white" : "text-slate-300"
        )}
      >
        {segment.text}
      </p>

      {segment.translation && (
        <div className="mt-2 p-3 bg-slate-900/50 rounded-md">
          <p className="text-sm text-slate-400">{segment.translation.zh}</p>
        </div>
      )}
    </div>
  )
}

import { CheckCircle, Merge, Edit, Save } from 'lucide-react'
import { cn, formatTimestamp } from '@/lib/utils'
import type { SentenceSegment } from '@/types/api'
import { useState, useEffect } from 'react'

interface SentenceItemProps {
  segment: SentenceSegment
  isActive: boolean
  onClick: () => void
  onMerge?: () => void
  onUpdate?: (text: string) => void
  index: number
}

export const SentenceItem = ({ segment, isActive, onClick, onMerge, onUpdate, index }: SentenceItemProps) => {
  const [isEditing, setIsEditing] = useState(false)
  const [editedText, setEditedText] = useState(segment.text)

  // 当 segment.text 改变时，同步更新 editedText
  useEffect(() => {
    setEditedText(segment.text)
  }, [segment.text])

  const handleEdit = () => {
    setIsEditing(true)
  }

  const handleSave = () => {
    setIsEditing(false)
    if (onUpdate && editedText !== segment.text) {
      onUpdate(editedText)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditedText(segment.text)
  }

  const handleMerge = () => {
    if (onMerge) {
      onMerge()
    }
  }

  return (
    <div
      onClick={onClick}
      className={cn(
        "p-4 rounded-lg border transition-all duration-200 cursor-pointer hover:bg-white/5 group",
        isActive
          ? "bg-primary/20 border-primary"
          : "bg-slate-800/50 border-slate-700/50"
      )}
    >
      {/* 操作按钮 - 默认隐藏，鼠标悬停时显示 */}
      <div className="absolute top-2 right-2 flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        {index > 0 && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleMerge()
            }}
            className="p-1.5 bg-blue-500/20 text-blue-400 rounded hover:bg-blue-500/30 transition-colors"
            title="合并到上一句"
          >
            <Merge className="w-4 h-4" />
          </button>
        )}
        {isEditing ? (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleSave()
            }}
            className="p-1.5 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30 transition-colors"
            title="保存"
          >
            <Save className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleEdit()
            }}
            className="p-1.5 bg-yellow-500/20 text-yellow-400 rounded hover:bg-yellow-500/30 transition-colors"
            title="编辑"
          >
            <Edit className="w-4 h-4" />
          </button>
        )}
      </div>

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
      </div>

      {isEditing ? (
        <textarea
          value={editedText}
          onChange={(e) => {
            e.stopPropagation()
            setEditedText(e.target.value)
          }}
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              handleCancel()
            } else if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              handleSave()
            }
          }}
          className="w-full p-3 bg-slate-900/50 border border-primary rounded-md text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
          rows={3}
          autoFocus
        />
      ) : (
        <>
          <p
            className={cn(
              "text-lg leading-relaxed",
              isActive ? "text-white" : "text-slate-300"
            )}
          >
            {segment.text}
          </p>

          {segment.translation && (
            <div className="mt-2 p-3 bg-slate-900/50 rounded-md">
              <p className="text-base text-slate-400">{segment.translation.zh}</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

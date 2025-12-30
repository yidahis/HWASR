import { useState, useRef, useEffect } from 'react'

interface PlaybackRange {
  start: number
  end: number
}

export const useAudioPlayer = () => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [playbackRange, setPlaybackRange] = useState<PlaybackRange | null>(null)
  const [isReady, setIsReady] = useState(false)
  const pendingPlay = useRef<{ start: number; end: number } | null>(null)
  const audioRef = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleTimeUpdate = () => {
      const currentTime = audio.currentTime
      setCurrentTime(currentTime)

      if (playbackRange && currentTime >= playbackRange.end) {
        audio.pause()
        setPlaybackRange(null)
      }
    }
    const handleLoadedMetadata = () => {
      setDuration(audio.duration)
      setIsReady(true)
    }
    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)
    const handleEnded = () => {
      setIsPlaying(false)
      setPlaybackRange(null)
    }
    const handleSeeked = () => {
      if (pendingPlay.current) {
        audio.play()
        pendingPlay.current = null
      }
    }

    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('play', handlePlay)
    audio.addEventListener('pause', handlePause)
    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('seeked', handleSeeked)

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('play', handlePlay)
      audio.removeEventListener('pause', handlePause)
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('seeked', handleSeeked)
    }
  }, [playbackRange])

  const play = () => {
    audioRef.current?.play()
  }

  const pause = () => {
    audioRef.current?.pause()
  }

  const toggle = () => {
    if (isPlaying) {
      pause()
    } else {
      playContinuous()
    }
  }

  const seek = (time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time
    }
  }

  const playRange = (start: number, end: number) => {
    if (audioRef.current && isReady) {
      console.log('playRange called:', { start, end, currentTime: audioRef.current.currentTime, isReady })
      setPlaybackRange({ start, end })
      pendingPlay.current = { start, end }
      audioRef.current.currentTime = start
    }
  }

  const playContinuous = () => {
    setPlaybackRange(null)
    audioRef.current?.play()
  }

  return {
    audioRef,
    isPlaying,
    currentTime,
    duration,
    isReady,
    play,
    pause,
    toggle,
    seek,
    playRange,
    playContinuous,
  }
}

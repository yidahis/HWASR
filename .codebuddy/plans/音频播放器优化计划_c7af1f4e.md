---
name: 音频播放器优化计划
overview: 优化音频播放器交互体验：1) 点击分句时只播放当前分句（从分句开始到结束）；2) 点击播放按钮时从当前时间开始连续播放直到音频结尾。需要修改 useAudioPlayer hook、ResultViewer 组件和相关交互逻辑。
todos:
  - id: update-hook-state
    content: 修改 useAudioPlayer hook，添加 playbackRange 状态和相关类型定义
    status: completed
  - id: implement-play-methods
    content: 实现 playRange 和 playContinuous 方法，区分分句播放和连续播放
    status: completed
    dependencies:
      - update-hook-state
  - id: add-range-check
    content: 在 timeUpdate 监听器中添加播放范围检查逻辑
    status: completed
    dependencies:
      - implement-play-methods
  - id: update-sentence-item
    content: 修改 SentenceItem 组件，点击分句时调用 playRange 方法
    status: completed
    dependencies:
      - implement-play-methods
  - id: update-result-viewer
    content: 修改 ResultViewer 组件，播放按钮调用 playContinuous 方法
    status: completed
    dependencies:
      - implement-play-methods
---

## Product Overview

优化现有音频播放器的交互逻辑，实现精细化的播放控制功能。用户需要两种不同的播放模式：点击分句时仅播放当前分句片段，点击播放按钮时从当前时间连续播放至音频结尾。

## Core Features

- 点击分句时，设置播放范围为当前分句的起止时间，播放结束后自动暂停
- 点击播放按钮时，从当前播放位置连续播放直到音频结束，不再每次从头开始
- 优化 useAudioPlayer hook，支持播放范围控制和连续播放状态管理
- 更新 ResultViewer 和 SentenceItem 组件的交互逻辑

## Tech Stack

- Frontend framework: React + TypeScript
- State management: React Hooks (useAudioPlayer)

## Tech Architecture

### System Architecture

- Architecture pattern: Hook-based state management with controlled audio playback
- Component structure: useAudioPlayer (Hook) → ResultViewer (Parent Component) → SentenceItem (Child Component)

### Module Division

- **useAudioPlayer Hook**: 核心音频播放逻辑，管理播放状态、播放范围、时间控制
- **ResultViewer Component**: 结果展示容器，协调播放按钮和分句列表的交互
- **SentenceItem Component**: 单个分句展示项，处理分句点击事件

### Data Flow

1. **分句播放**: 用户点击分句 → 获取分句起止时间 → Hook 设置播放范围 → 播放至结束时间自动暂停
2. **连续播放**: 用户点击播放按钮 → Hook 清除播放范围限制 → 从当前时间播放至音频结束

## Implementation Details

### Key Code Structures

**播放范围控制接口**:

```typescript
interface PlaybackRange {
  start: number;  // 起始时间（秒）
  end: number;    // 结束时间（秒）
}
```

**Hook 状态结构**:

```typescript
interface AudioPlayerState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  playbackRange: PlaybackRange | null;  // null 表示无范围限制
}
```

**核心播放逻辑**:

```typescript
// 设置播放范围（用于分句播放）
const playRange = (start: number, end: number) => {
  setPlaybackRange({ start, end });
  audioRef.current.currentTime = start;
  audioRef.current.play();
};

// 连续播放（用于播放按钮）
const playContinuous = () => {
  setPlaybackRange(null);  // 清除范围限制
  audioRef.current.play();
};

// 监听播放进度
useEffect(() => {
  const handleTimeUpdate = () => {
    const currentTime = audioRef.current.currentTime;
    setCurrentTime(currentTime);
    
    // 检查是否超出播放范围
    if (playbackRange && currentTime >= playbackRange.end) {
      audioRef.current.pause();
    }
  };
  
  audioElement.addEventListener('timeupdate', handleTimeUpdate);
  return () => audioElement.removeEventListener('timeupdate', handleTimeUpdate);
}, [playbackRange]);
```

### Technical Implementation Plan

1. **问题陈述**: 当前播放逻辑无法区分分句播放和连续播放两种模式
2. **解决方案**: 在 useAudioPlayer 中引入 playbackRange 状态，区分两种播放模式
3. **关键实现**:

- 添加 playbackRange 状态管理
- 实现 playRange 方法用于分句播放
- 修改 play/pause 方法支持连续播放
- 在 timeUpdate 监听器中检查播放范围

4. **实现步骤**:

- 修改 useAudioPlayer hook，添加 playbackRange 状态
- 实现 playRange 和 playContinuous 方法
- 更新 SentenceItem 调用 playRange
- 更新播放按钮调用 playContinuous

5. **测试策略**: 测试分句播放是否在结束时暂停，测试连续播放是否正常到结尾
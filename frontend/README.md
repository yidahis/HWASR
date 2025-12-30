# Whisper ASR 前端应用

基于 Vite + React + TypeScript 构建的语音识别前端应用，集成现代 UI 设计。

## 技术栈

- Vite 5
- React 18
- TypeScript 5
- Tailwind CSS 3.4
- Axios

## 安装

```bash
cd frontend
npm install
```

## 开发

```bash
npm run dev
```

访问 http://localhost:5173

## 构建

```bash
npm run build
```

## 功能特性

- 音频文件拖拽上传
- 实时任务状态轮询
- 说话人识别与标签显示
- 精确时间戳跳转
- 音频播放器集成
- JSON 结果导出

## 目录结构

```
src/
├── components/       # UI 组件
├── hooks/           # 自定义 Hooks
├── lib/             # 工具函数
├── services/         # API 调用
├── types/           # TypeScript 类型定义
├── App.tsx          # 主应用组件
└── main.tsx         # 入口文件
```

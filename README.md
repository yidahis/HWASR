# HW_ASR - 智能语音识别系统

一个基于 Whisper 和 Pyannote 的智能语音识别系统，支持说话人分离、多语言翻译和音频编辑功能。

## 功能特性

### 核心功能
- 🎤 **语音识别**: 使用 Faster-Whisper 模型进行高精度语音识别
- 👥 **说话人分离**: 基于语音特征自动识别不同说话人
- 🌐 **多语言翻译**: 支持 100+ 种语言的自动翻译（基于 deep-translator）
- 📝 **实时编辑**: 在线编辑识别结果，自动重新翻译修改的内容
- 🔊 **音频播放**: 可视化音频播放，支持点击句子定位播放位置
- 🔗 **句子合并**: 支持合并相邻的识别句子
- 📚 **历史记录**: 保存所有识别结果，支持查看和下载

### 技术特点
- 异步处理：上传后后台处理，不阻塞用户操作
- 进度追踪：实时显示处理进度
- 文件下载：支持下载 JSON 格式的识别结果
- 音频流式传输：支持 Range 请求，优化音频加载体验

## 项目结构

```
HW_ASR/
├── backend/                 # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── services/       # 业务逻辑服务
│   │   ├── models/         # 数据模型
│   │   ├── utils/          # 工具函数
│   │   └── core/           # 配置文件
│   ├── storage/            # 数据存储目录
│   │   ├── uploads/        # 上传文件
│   │   ├── results/        # 识别结果
│   │   └── audio_processed/# 处理后的音频
│   ├── requirements.txt    # Python 依赖
│   └── .env                # 环境变量配置
├── frontend/               # 前端应用 (React + Vite)
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── services/       # API 服务
│   │   ├── types/          # TypeScript 类型定义
│   │   └── lib/            # 工具函数
│   └── package.json        # Node.js 依赖
├── logs/                   # 运行日志
├── start.py                # 一键启动脚本
└── start.sh                # Shell 启动脚本
```

## 技术栈

### 后端
- **FastAPI**: 现代、快速的 Python Web 框架
- **Uvicorn**: ASGI 服务器
- **Faster-Whisper**: 高性能语音识别模型
- **Pyannote.audio**: 说话人分离模型
- **Deep-Translator**: 多语言翻译服务
- **Pydub**: 音频处理
- **Librosa**: 音频分析

### 前端
- **React 18**: 用户界面框架
- **TypeScript**: 类型安全的 JavaScript
- **Vite**: 快速的构建工具
- **Tailwind CSS**: 实用优先的 CSS 框架
- **Lucide React**: 图标库
- **Axios**: HTTP 客户端

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 18+
- npm 或 yarn

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd HW_ASR
```

#### 2. 配置后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制示例文件并修改）
cp .env.example .env
```

#### 3. 配置前端

```bash
cd frontend

# 安装依赖
npm install
```

### 启动服务

#### 方式一：使用 Python 启动脚本（推荐）

```bash
# 在项目根目录
python start.py
```

这个脚本会同时启动前后端服务，并自动管理进程。

#### 方式二：使用 Shell 脚本（Linux/macOS）

```bash
bash start.sh
```

#### 方式三：手动启动

**启动后端**:
```bash
cd backend
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

**启动前端**（新终端）:
```bash
cd frontend
npm run dev
```

### 访问应用

- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8003
- **API 文档**: http://localhost:8003/docs

## 使用说明

### 1. 上传音频

- 支持的格式：MP3, WAV, M4A, OGG, FLAC
- 最大文件大小：100MB（可配置）
- 点击上传区域选择文件或拖拽文件上传

### 2. 处理过程

- 上传后自动开始处理
- 实时显示处理进度
- 处理步骤：初始化 → 音频处理 → 语音识别 → 说话人分离 → 翻译 → 完成

### 3. 查看结果

- 查看完整的识别文本
- 按说话人分组显示句子
- 显示每个句子的时间戳
- 显示翻译结果（中文和原文）

### 4. 编辑功能

- **编辑句子**: 点击编辑按钮修改句子内容，自动重新翻译
- **合并句子**: 点击合并按钮将当前句子与下一句合并
- **播放音频**: 点击句子播放对应音频片段
- **下载结果**: 下载 JSON 格式的完整识别结果

### 5. 历史记录

- 点击右上角时钟图标查看历史记录
- 查看所有已处理的识别结果
- 快速加载历史结果

## API 文档

### 主要接口

#### 上传音频
```
POST /api/upload
Content-Type: multipart/form-data

Response:
{
  "task_id": "uuid",
  "status": "pending",
  "progress": 0.0,
  "message": "文件上传成功，开始处理"
}
```

#### 查询任务状态
```
GET /api/status/{task_id}

Response:
{
  "task_id": "uuid",
  "status": "processing",
  "progress": 50.0,
  "message": "正在处理音频..."
}
```

#### 获取识别结果
```
GET /api/result/{result_id}

Response:
{
  "success": true,
  "result_id": "uuid",
  "text": "完整识别文本",
  "sentences": [...],
  "speakers": [0, 1, 2],
  "total_duration": 120.5
}
```

#### 更新结果
```
POST /api/update/{result_id}
Content-Type: application/json

Body:
{
  "sentences": [...]
}
```

更多 API 详情请访问 http://localhost:8003/docs

## 配置说明

### 后端配置 (.env)

```env
# 是否启用说话人分离
ENABLE_DIARIZATION=true

# Whisper 模型
WHISPER_MODEL=base

# 最大文件大小 (MB)
MAX_FILE_SIZE=100
```

### 前端配置

前端通过环境变量配置 API 地址，默认为 `http://localhost:8003`

## 开发说明

### 后端开发

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### 前端开发

```bash
cd frontend
npm run dev
```

### 代码规范

- 后端：遵循 PEP 8 规范
- 前端：使用 ESLint 进行代码检查
- 使用 TypeScript 的严格模式

## 常见问题

### Q: 处理速度慢怎么办？
A: 可以更换更快的 Whisper 模型（如 small, base），或者使用 GPU 加速。

### Q: 说话人分离不准确？
A: 可以调整 Pyannote.audio 的模型参数，或者确保音频质量较好。

### Q: 翻译不准确？
A: 可以修改翻译服务源代码，使用其他翻译 API（如 Google Translate, DeepL 等）。

### Q: 内存占用过高？
A: 可以在处理完成后卸载模型，或者使用更小的模型。

## 性能优化建议

1. **使用 GPU 加速**: 安装 CUDA 版本的 PyTorch
2. **模型选择**: 根据需求选择合适大小的 Whisper 模型
3. **音频预处理**: 上传前转换为 WAV 格式可加快处理速度
4. **批量处理**: 可以修改代码支持批量上传处理

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请通过 GitHub Issues 联系。

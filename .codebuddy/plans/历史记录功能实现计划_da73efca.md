---
name: 历史记录功能实现计划
overview: 在首页添加历史记录按钮，点击后弹出模态视图展示历史记录列表，支持选择加载历史记录。需要修改前端添加历史记录列表API、模态组件，后端添加获取历史记录接口。
design:
  architecture:
    framework: react
    component: mui
  styleKeywords:
    - Material Design
    - Clean
    - Minimalist
  fontSystem:
    fontFamily: Roboto
    heading:
      size: 24px
      weight: 500
    subheading:
      size: 16px
      weight: 400
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#1976D2"
    background:
      - "#FFFFFF"
      - "#F5F5F5"
    text:
      - "#333333"
      - "#666666"
    functional:
      - "#4CAF50"
      - "#F44336"
todos:
  - id: create-history-types
    content: 创建 HistoryItem 和 HistoryDetail 类型定义
    status: completed
  - id: implement-history-api
    content: 实现后端历史记录列表和详情接口
    status: completed
  - id: create-history-modal
    content: 开发前端历史记录模态框组件
    status: completed
  - id: integrate-button
    content: 在首页添加历史记录入口按钮
    status: completed
  - id: connect-api-logic
    content: 连接前端 API 调用与后端数据交互
    status: completed
---

## Product Overview

在现有首页添加历史记录功能，允许用户查看并加载过往的语音识别结果。通过模态视图交互，保持页面简洁性，提供便捷的历史数据回溯能力。

## Core Features

- 首页增加"历史记录"入口按钮
- 弹出模态视图展示历史记录列表
- 列表支持显示历史记录元信息（文件名、时间等）
- 点击列表项加载选中的历史记录数据
- 后端提供历史记录文件扫描与读取接口

## Tech Stack

- **前端框架**: React + TypeScript
- **样式库**: Tailwind CSS
- **后端框架**: FastAPI (Python)
- **数据存储**: 本地文件系统 (/backend/storage/results)

## 架构设计

### 系统架构

采用前后端分离架构。前端负责交互展示，后端负责文件扫描与数据读取。

```mermaid
graph LR
    A[用户点击历史记录按钮] --> B[前端请求历史列表API]
    B --> C[后端扫描results目录]
    C --> D[返回文件列表元数据]
    D --> E[前端渲染模态列表]
    E --> F[用户选择记录]
    F --> G[前端请求详情API]
    G --> H[后端读取JSON/WAV文件]
    H --> I[返回完整数据]
    I --> J[前端加载并展示]
```

### 模块划分

- **前端模块**:
- `HistoryButton`: 首页入口组件
- `HistoryModal`: 历史记录模态框组件
- `historyService`: 封装历史记录相关API调用
- **后端模块**:
- `/api/history/list`: 获取历史记录列表接口
- `/api/history/load`: 加载指定历史记录详情接口

### 数据流

1. 列表获取流程: 前端调用 GET /api/history/list -> 后端遍历目录 -> 返回文件名及创建时间数组 -> 前端展示。
2. 详情加载流程: 前端调用 GET /api/history/load?filename=xxx -> 后端解析JSON -> 返回识别结果及音频路径 -> 前端回填状态。

## 实现细节

### 目录结构

```
src/
├── components/
│   ├── HistoryButton.tsx      # 新增：历史记录入口按钮
│   └── HistoryModal.tsx       # 新增：历史记录列表模态框
├── services/
│   └── historyApi.ts          # 新增：历史记录API封装
└── types/
    └── history.ts             # 新增：历史记录类型定义

backend/
├── routers/
│   └── history.py             # 新增：历史记录路由
└── services/
    └── storage_service.py     # 修改：增加文件读取逻辑
```

### 关键代码结构

**类型定义 (history.ts)**:

```typescript
export interface HistoryItem {
  filename: string;
  createdAt: string;
}

export interface HistoryDetail {
  text: string;
  audioPath: string;
  // 其他识别结果字段
}
```

**API接口 (historyApi.ts)**:

```typescript
export const fetchHistoryList = async (): Promise<HistoryItem[]> => {
  return request.get('/api/history/list');
};

export const loadHistoryItem = async (filename: string): Promise<HistoryDetail> => {
  return request.get(`/api/history/load`, { params: { filename } });
};
```

**后端路由 (history.py)**:

```python
@router.get("/list")
async def get_history_list():
    # 扫描 storage/results 目录，返回元数据列表
    pass

@router.get("/load")
async def load_history(filename: str):
    # 读取指定 JSON 文件内容并返回
    pass
```

## 技术实施计划

1. **问题**: 需在不改动现有核心逻辑下平滑植入功能。
2. **方案**: 独立组件化开发，API解耦。
3. **关键步骤**:

- 定义前后端数据契约。
- 实现后端文件扫描逻辑。
- 开发前端模态组件与API对接。
- 集成至首页布局。

4. **测试策略**: 模拟空目录、多文件场景，验证加载与回显正确性。

## 集成点

- **组件集成**: `HistoryButton`挂载至首页导航区或操作栏。
- **数据格式**: JSON传输，包含文件名与时间戳。
- **认证**: 复用现有中间件（如有）。

## 设计风格

采用现代简洁的 Material Design 风格。使用 MUI 组件库构建模态视图，确保与现有页面风格统一。视觉上强调清晰的层级与舒适的交互反馈。

## 页面规划

### 首页 (Home)

- **顶部导航区**: 右侧增加"历史记录"图标按钮。
- **历史记录模态框**:
- **头部**: 标题"历史记录"及关闭按钮。
- **列表区**: 展示历史记录项，每项包含文件名、时间戳及"加载"操作按钮。
- **空状态**: 无记录时显示友好提示图文。
- **底部**: 可选的分页或加载更多（视数据量而定）。
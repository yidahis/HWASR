---
name: fix-numpy-compatibility
overview: 修复 NumPy 2.0 与 pyannote.audio 的兼容性问题，使说话人识别功能正常工作。
todos:
  - id: locate-nan-usage
    content: 使用 [subagent:code-explorer] 搜索项目中所有使用 np.NaN 的文件
    status: completed
  - id: fix-nan-references
    content: 将所有 np.NaN 替换为 np.nan
    status: completed
    dependencies:
      - locate-nan-usage
  - id: verify-model-loading
    content: 测试 pyannote.audio 模型加载功能
    status: completed
    dependencies:
      - fix-nan-references
  - id: validate-asr-pipeline
    content: 验证完整的说话人识别流程
    status: completed
    dependencies:
      - verify-model-loading
---

## Product Overview

修复项目中 pyannote.audio 说话人识别模块与 NumPy 2.0 版本的兼容性错误，确保核心功能正常运行。

## Core Features

- 修复 `np.NaN` 引用的兼容性问题（替换为 `np.nan`）
- 验证说话人识别模型加载流程
- 确保代码在 NumPy 2.0 环境下稳定运行

## Tech Stack

- Python 环境
- 依赖库：NumPy (2.0+), pyannote.audio

## Tech Architecture

### System Architecture

- 定位并修复代码中直接引用已弃用的 NumPy 常量
- 范围：涉及 pyannote.audio 模型加载及预处理的相关脚本

### Module Division

- **兼容性修复模块**：处理 NumPy 版本升级导致的 API 变更
- **模型加载模块**：验证 pyannote.audio 模型的初始化流程

### Data Flow

代码扫描 → 识别 `np.NaN` 使用位置 → 替换为 `np.nan` → 运行时测试验证

## Implementation Details

### Core Directory Structure

由于是对现有项目的兼容性修复，主要关注可能受影响的文件：

```
project-root/
├── src/
│   ├── utils/              # 可能包含数据预处理工具
│   ├── models/             # 模型加载逻辑
│   └── main.py             # 主入口文件
```

### Key Code Structures

**修复策略**：
将代码中的 `np.NaN` 替换为 NumPy 推荐的 `np.nan`。

**修复前代码**：

```python
import numpy as np
# 错误代码示例
value = np.NaN
```

**修复后代码**：

```python
import numpy as np
# 正确代码示例
value = np.nan
```

### Technical Implementation Plan

1. **问题定位**：全项目搜索 `np.NaN` 字符串，定位所有受影响文件。
2. **代码替换**：将所有 `np.NaN` 统一替换为 `np.nan`。
3. **依赖检查**：检查 `pyannote.audio` 及相关库版本是否支持 NumPy 2.0，必要时降级 NumPy 或升级相关库。
4. **功能验证**：运行说话人识别测试脚本，确认模型加载和推理无报错。

### Integration Points

- 涉及与 NumPy 库的直接交互
- 可能影响 pyannote.audio 的内部数据处理逻辑

## Technical Considerations

### Performance Optimization

- 确保替换后的代码性能与之前保持一致，`np.nan` 与 `np.NaN` 在功能上完全等价。

### Security Measures

- 确保代码修改不引入新的安全漏洞。

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 在项目文件系统中搜索所有包含 `np.NaN` 的文件，定位具体的代码行和上下文。
- Expected outcome: 提供详细的文件列表和代码位置，以便进行精准修复。
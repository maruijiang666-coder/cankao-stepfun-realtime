# Stepfun Realtime API Web Demo

这是一个基于 Stepfun Realtime API 的实时语音对话演示项目。支持 **Manual Mode (手动模式/按住说话)** 和 **VAD Mode (语音自动检测)**。

## 功能特性

- **双模式切换**:
  - **Manual Mode (PTT)**: 按住按钮说话，松开即发送并获取回复。适合嘈杂环境或需要精准控制的场景。
  - **VAD Mode**: 自动检测用户说话开始和结束，实现全双工自然对话。
- **实时反馈**: 界面显示实时语音转文字 (STT) 内容和 AI 回答内容。
- **低延迟**: 采用原生 AudioWorklet 处理 PCM 音频流，WebSocket 实现全双工通信。
- **音频控制**: 支持用户说话时自动中断 (Interrupt) AI 的语音输出。

## 技术栈

- **后端**: Python 3.10+, FastAPI, aiohttp (WebSocket 代理)
- **前端**: HTML5, Vanilla JavaScript, AudioWorklet API
- **模型**: Stepfun Realtime API (`step-audio-2`)

## 快速开始

### 1. 环境准备

确保已安装 Python 3.10 或更高版本。

### 2. 安装依赖

进入项目目录，安装 Python 依赖：

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置 API Key

在 `backend` 目录下创建 `.env` 文件（或直接在前端界面输入）：
```env
API_KEY=你的阶跃星辰API_KEY
```

### 4. 启动后端

```bash
python main.py
```
后端将运行在 `http://localhost:8080`，并作为 Stepfun API 的 WebSocket 代理。

### 5. 运行前端

由于浏览器安全限制，建议使用 Live Server (VS Code 插件) 或简单的 HTTP 服务打开 `frontend/index.html`：

```bash
# 例如使用 python
cd frontend
python -m http.server 8000
```
然后在浏览器访问 `http://localhost:8000`。

## 使用说明

1. **连接**: 输入 API Key 后点击 **Connect**。
2. **模式选择**:
   - **Manual (推荐)**: 默认模式。按住下方的蓝色麦克风按钮开始说话，松开按钮 AI 会立即响应。
   - **VAD**: 切换后 AI 会自动监听声音，无需操作按钮。
3. **中断 AI**: 在 AI 说话时，如果你直接按住按钮开始说话，AI 的声音会立即停止。

## 项目结构

- `backend/main.py`: FastAPI 实现的 WebSocket 代理服务。
- `frontend/index.html`: 主界面及核心逻辑。
- `frontend/audio-processor.js`: AudioWorklet 处理器，负责采集麦克风原始 PCM 数据。
- `frontend/wav-stream-player.js`: 负责播放 AI 返回的流式 PCM 音频。

## 注意事项

- 请确保使用 HTTPS 环境或 `localhost` 访问，否则浏览器无法获取麦克风权限。
- 推荐使用 Chrome 或 Edge 浏览器以获得最佳音频处理效果。

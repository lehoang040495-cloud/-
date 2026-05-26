# 景区导览服务 AI 数字人 - 后端

基于 **FastAPI + 豆包大模型 + RAG 知识库 + TTS/STT** 的智能景区导览后端系统。

## 技术栈

| 模块 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn（异步） |
| 大模型 | 豆包代理网关 / DeepSeek API（可切换） |
| 知识库 | FAISS + sentence-transformers 向量检索 |
| 语音合成 | Edge-TTS |
| 语音识别 | faster-whisper |
| 数据库 | SQLite + SQLAlchemy（异步） |

## 快速启动

### 环境要求

- Python 3.10+
- Windows / Linux / macOS

### 安装与运行

```bash
# 1. 克隆项目
git clone https://github.com/lehoang040495-cloud/-.git scenic-guide-backend
cd scenic-guide-backend

# 2. 复制配置文件
cp .env.example .env        # Linux/macOS
copy .env.example .env      # Windows

# 3. 一键启动（自动创建虚拟环境 + 安装依赖 + 运行）
# Windows:
start.bat
# Linux/macOS:
chmod +x start.sh && ./start.sh

# 4. 初始化默认数据（首次运行，另开终端执行）
python init_data.py
```

启动成功后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 手动启动

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 配置说明

编辑 `.env` 文件进行配置：

```ini
# 大模型选择：doubao（默认） / deepseek
LLM_PROVIDER=doubao

# 豆包代理网关（已内置，无需修改）
DOUBAO_ENDPOINT=https://fosp-gateway.vemic.com/ai_proxy/v2/volces/chat/completions
DOUBAO_MODEL=doubao-seed-2-0-pro-260215
DOUBAO_OPEN_ID=xxx
DOUBAO_DEVELOPER_SECRET=xxx

# DeepSeek（备用，需要 API Key）
# LLM_PROVIDER=deepseek
# DEEPSEEK_API_KEY=sk-xxxxx

# 语音配置
TTS_VOICE=zh-CN-XiaoxiaoNeural
WHISPER_MODEL=base
```

## API 接口

### 游客端

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/chat` | 智能对话（RAG 增强） |
| POST | `/api/chat/route` | 个性化路线推荐 |
| POST | `/api/speech/tts` | 文字转语音 |
| POST | `/api/speech/stt` | 语音转文字 |
| GET | `/api/speech/voices` | 获取可用语音列表 |
| GET | `/api/avatar/active` | 获取当前数字人配置 |

### 管理后台

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/knowledge` | 列出知识库文档 |
| POST | `/api/knowledge/upload` | 上传知识文档 |
| DELETE | `/api/knowledge/{id}` | 删除文档 |
| POST | `/api/knowledge/reindex` | 重建索引 |
| GET | `/api/avatar` | 列出数字人形象 |
| POST | `/api/avatar` | 创建形象配置 |
| POST | `/api/avatar/{id}/activate` | 切换形象 |
| GET | `/api/analytics/dashboard` | 数据大屏统计 |
| GET | `/api/analytics/sentiment-report` | 情感分析报告 |
| POST | `/api/analytics/feedback` | 提交游客反馈 |
| GET | `/api/analytics/hot-topics` | 热门话题 |

## 请求示例

### 智能对话

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "介绍一下这个景区的历史", "session_id": "user001"}'
```

响应：
```json
{
  "reply": "这个景区有着悠久的历史...",
  "session_id": "user001",
  "source": "rag",
  "response_time": 2.35
}
```

### 文字转语音

```bash
curl -X POST http://localhost:8000/api/speech/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "欢迎来到我们的景区"}'
```

响应：
```json
{
  "audio_url": "/audio/xxxxx.mp3"
}
```

### 上传知识库文档

```bash
curl -X POST http://localhost:8000/api/knowledge/upload \
  -F "file=@景区介绍.pdf" \
  -F "title=景区介绍" \
  -F "category=景点介绍"
```

### 数据大屏

```bash
curl http://localhost:8000/api/analytics/dashboard
```

响应：
```json
{
  "today_chats": 128,
  "today_users": 45,
  "week_chats": 856,
  "week_users": 234,
  "avg_rating": 4.5,
  "positive_rate": 87.5,
  "top_questions": [...],
  "satisfaction_trend": [...],
  "daily_chat_trend": [...]
}
```

## 项目结构

```
scenic-guide-backend/
├── app/
│   ├── main.py                 # FastAPI 入口 + CORS
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   ├── models.py               # 数据模型（6张表）
│   ├── schemas.py              # 请求/响应模式
│   ├── api/
│   │   ├── chat.py             # 对话接口
│   │   ├── knowledge.py        # 知识库管理
│   │   ├── avatar.py           # 数字人配置
│   │   ├── speech.py           # 语音接口
│   │   └── analytics.py        # 数据分析
│   └── services/
│       ├── llm_service.py      # 大模型调用（豆包/DeepSeek）
│       ├── rag_service.py      # RAG 检索增强生成
│       ├── tts_service.py      # 语音合成
│       ├── stt_service.py      # 语音识别
│       └── analytics_service.py # 统计分析
├── data/                       # 运行时数据（自动创建）
├── requirements.txt
├── .env.example
├── init_data.py                # 初始化默认数据
├── start.bat / start.sh        # 一键启动脚本
└── README.md
```

## 知识库使用

1. 准备景区资料文档（支持 PDF、Word、TXT、Excel、Markdown、JSON）
2. 通过 `/api/knowledge/upload` 上传文档
3. 系统自动切分文本、生成向量、存入 FAISS 索引
4. 对话时自动检索相关知识片段，辅助大模型回答

## 前端对接

前端调用示例（Vue3 + Axios）：

```javascript
// 发送对话
const res = await axios.post('http://localhost:8000/api/chat', {
  message: userInput,
  session_id: sessionId
})

// 获取语音
const ttsRes = await axios.post('http://localhost:8000/api/speech/tts', {
  text: res.data.reply
})

// 播放语音
const audio = new Audio('http://localhost:8000' + ttsRes.data.audio_url)
audio.play()
```

## 切换大模型

编辑 `.env` 文件：

```ini
# 使用豆包（默认）
LLM_PROVIDER=doubao

# 使用 DeepSeek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxxxx
```

重启服务即可生效。

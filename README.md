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
| POST | `/api/chat` | 智能对话（RAG 增强，支持模式切换） |
| POST | `/api/chat/route` | 个性化路线推荐 |
| POST | `/api/speech/tts` | 文字转语音 |
| POST | `/api/speech/stt` | 语音转文字 |
| GET | `/api/speech/voices` | 获取可用语音列表 |
| GET | `/api/avatar/active` | 获取当前数字人配置 |
| GET | `/api/weather` | 查询天气（自动推荐游览建议） |
| POST | `/api/vision/recognize` | 拍照识景（看景即讲） |

### 出行伴侣助手

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/companion` | 智能出行问答 |
| POST | `/api/companion/emergency` | 紧急求助 |
| GET | `/api/companion/services` | 附近服务设施查询 |
| GET | `/api/companion/reminders` | 游览温馨提示 |
| GET | `/api/companion/pitfall-guide` | 避坑指南 |

### 游览轨迹与纪念

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/trajectory/record` | 记录游览景点 |
| GET | `/api/trajectory/list/{session_id}` | 获取游览轨迹 |
| GET | `/api/trajectory/card/{session_id}` | 生成旅行纪念卡片 |
| DELETE | `/api/trajectory/clear/{session_id}` | 清除游览记录 |

### 智能关怀

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/care/generate/{session_id}` | 生成关怀消息 |
| GET | `/api/care/messages/{session_id}` | 获取关怀消息列表 |
| GET | `/api/care/check/{session_id}` | 检查未读关怀 |
| POST | `/api/care/messages/{id}/read` | 标记已读 |

### 游客画像

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/analytics/profile/{session_id}` | 获取游客画像分析 |
| GET | `/api/analytics/profiles` | 游客画像列表 |

### 管理后台

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/knowledge` | 列出知识库文档 |
| POST | `/api/knowledge/upload` | 上传知识文档 |
| DELETE | `/api/knowledge/{id}` | 删除文档 |
| POST | `/api/knowledge/reindex` | 重建索引 |
| GET | `/api/avatar` | 列出数字人形象 |
| POST | `/api/avatar` | 创建形象配置 |
| PUT | `/api/avatar/{id}` | 更新形象（含模式切换） |
| POST | `/api/avatar/{id}/activate` | 切换形象 |
| GET | `/api/analytics/dashboard` | 数据大屏统计 |
| GET | `/api/analytics/sentiment-report` | 情感分析报告 |
| POST | `/api/analytics/feedback` | 提交游客反馈 |
| GET | `/api/analytics/hot-topics` | 热门话题 |

## 特色功能

### 老人/儿童专属模式
通过 Avatar 的 `mode` 字段切换对话风格：
- `normal`：标准模式
- `elderly`：老人模式（简单易懂、关注安全和休息）
- `children`：儿童模式（生动有趣、寓教于乐）

```bash
# 切换到老人模式
curl -X PUT http://localhost:8000/api/avatar/1 \
  -H "Content-Type: application/json" \
  -d '{"mode": "elderly"}'
```

### 拍照识景（看景即讲）
上传照片即可识别景点并获得讲解：

```bash
curl -X POST http://localhost:8000/api/vision/recognize \
  -F "image=@景点照片.jpg"
```

### 旅行纪念卡片
记录游览轨迹，自动生成纪念文字：

```bash
# 记录景点
curl -X POST http://localhost:8000/api/trajectory/record \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user001", "spot_name": "望江楼", "visit_order": 1}'

# 生成纪念卡片
curl http://localhost:8000/api/trajectory/card/user001
```

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

### 天气查询

```bash
curl http://localhost:8000/api/weather
```

响应：
```json
{
  "location": "景区",
  "temperature": "28°C",
  "description": "晴",
  "humidity": "55%",
  "wind": "5.2 km/h",
  "suggestion": "天气晴朗，适合游览！记得涂防晒霜和带水。"
}
```

### 文字转语音

```bash
curl -X POST http://localhost:8000/api/speech/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "欢迎来到我们的景区"}'
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

## 项目结构

```
scenic-guide-backend/
├── app/
│   ├── main.py                 # FastAPI 入口 + CORS
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   ├── models.py               # 数据模型（9张表）
│   ├── schemas.py              # 请求/响应模式
│   ├── api/
│   │   ├── chat.py             # 对话接口（支持模式切换）
│   │   ├── knowledge.py        # 知识库管理
│   │   ├── avatar.py           # 数字人配置（含老人/儿童模式）
│   │   ├── speech.py           # 语音接口
│   │   ├── analytics.py        # 数据分析
│   │   ├── weather.py          # 天气查询
│   │   ├── companion.py        # 出行伴侣助手
│   │   ├── trajectory.py       # 游览轨迹+纪念卡片
│   │   ├── care.py             # 智能关怀
│   │   ├── vision.py           # 拍照识景
│   │   └── profile.py          # 游客画像分析
│   └── services/
│       ├── llm_service.py      # 大模型调用（豆包/DeepSeek）
│       ├── rag_service.py      # RAG 检索增强生成
│       ├── tts_service.py      # 语音合成
│       ├── stt_service.py      # 语音识别
│       ├── analytics_service.py # 统计分析
│       └── weather_service.py  # 天气服务
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

// 查询天气
const weather = await axios.get('http://localhost:8000/api/weather')

// 拍照识景
const formData = new FormData()
formData.append('image', photoFile)
const vision = await axios.post('http://localhost:8000/api/vision/recognize', formData)

// 记录游览轨迹
await axios.post('http://localhost:8000/api/trajectory/record', {
  session_id: sessionId,
  spot_name: '望江楼',
  visit_order: 1
})

// 生成纪念卡片
const card = await axios.get(`http://localhost:8000/api/trajectory/card/${sessionId}`)
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

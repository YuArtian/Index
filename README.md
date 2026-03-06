# Index - 个人学习助手

RAG 知识库 + Claude Chat + 学习进度追踪。

## 特性

- 🔍 **语义搜索** - 基于 pgvector 的向量相似度搜索
- 💬 **AI 对话** - Claude Chat + Tool Use RAG，自动检索知识库
- 📚 **学习进度** - 书目管理，阅读进度追踪
- 📄 **多格式上传** - PDF、Word、Excel、CSV、Markdown、图片、Jupyter Notebook
- 🔌 **可插拔架构** - Embedding/Storage/Parser 均可替换
- 🏠 **本地优先** - 支持本地 Embedding 模型，无需在线 API

## 快速启动

```bash
docker compose up -d db                                    # 1. 数据库 (:5432)
cd apps/api && source .venv/bin/activate && python main.py  # 2. 后端 (:8000)
cd apps/web && pnpm dev                                     # 3. 前端 (:5173)
```

## 项目结构

```
Index/
├── apps/
│   ├── api/                    # FastAPI 后端 (Python 3.13)
│   │   ├── main.py             # 入口
│   │   └── src/
│   │       ├── config.py       # pydantic-settings 配置
│   │       ├── database.py     # SQLAlchemy async engine
│   │       ├── models/         # ORM: Document, Chunk, Conversation, Message, LearningItem
│   │       ├── api/
│   │       │   ├── app.py      # 工厂函数 (lifespan + CORS + 服务注入)
│   │       │   ├── models.py   # Pydantic 请求/响应模型
│   │       │   └── routers/    # knowledge, chat, conversations, progress
│   │       ├── services/       # 业务逻辑: Knowledge, Search, Chat, Progress
│   │       └── providers/      # 可插拔: embedding/, storage/, parser/
│   │
│   └── web/                    # React 19 + Vite + TypeScript
│       └── src/
│           ├── router.tsx      # /chat, /knowledge, /progress
│           ├── pages/          # Chat, Knowledge, Progress
│           ├── components/     # layout/, chat/
│           ├── stores/         # Zustand + Immer
│           ├── api/            # chat.ts, knowledge.ts, progress.ts
│           └── service/        # request.ts, sse.ts
│
├── infra/db/init.sql           # 5 张表 + pgvector 索引
├── docker-compose.yml
├── .env                        # 运行时配置 (不入版本控制)
└── .env.example                # 配置模板
```

## 技术栈

| 层 | 选择 |
|---|---|
| 后端 | FastAPI + SQLAlchemy 2.0 async + pgvector |
| 数据库 | PostgreSQL 17 + pgvector (Docker) |
| AI Chat | Anthropic SDK (Claude Sonnet, Tool Use for RAG) |
| Embedding | 多 provider: Local (bge-large-zh) / Voyage AI / OpenAI / SiliconFlow |
| 前端 | React 19 + Vite + TypeScript + TailwindCSS 4 |
| 状态管理 | Zustand + Immer |
| HTTP | Axios + SSE (fetch streaming) |

## 环境变量 (.env)

```bash
DATABASE__URL=postgresql+asyncpg://postgres:postgres@localhost:5432/index

# Embedding: "local" | "voyage" | "openai" | "siliconflow"
EMBEDDING__PROVIDER=local
EMBEDDING__MODEL=BAAI/bge-large-zh-v1.5

# Claude Chat
ANTHROPIC_API_KEY=sk-ant-xxxx

CHUNK_SIZE=500
CHUNK_OVERLAP=50
CORS_ORIGINS=["http://localhost:5173"]
```

## 安装依赖

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate

# 基础依赖
pip install -e .

# 本地 Embedding 模型
pip install -e ".[local]"

# 高质量 PDF 模式 (Claude Vision 逐页识别)
pip install -e ".[pdf-vision]"
```

## 支持的文件格式

| 格式 | 扩展名 | 说明 |
|---|---|---|
| 文本 | .txt, .md | 直接读取 |
| PDF | .pdf | pypdf 提取 / 高质量模式 (Claude Vision) |
| Word | .docx | python-docx 解析 |
| 表格 | .csv, .xlsx, .xls | 逐行提取 |
| Notebook | .ipynb | 解析 code + markdown cell |
| 图片 | .jpg, .png, .gif, .webp, .bmp, .tiff | Claude Vision 识别 |

## API 端点

| 路由 | 端点 | 说明 |
|---|---|---|
| knowledge | `GET /` | 健康检查 + 统计 |
| | `POST /index` | 索引文档 (文本) |
| | `POST /upload` | 上传文件 (支持高质量模式) |
| | `POST /search` | 语义搜索 |
| | `GET /documents` | 文档列表 |
| | `DELETE /documents/{id}` | 删除文档 |
| chat | `POST /chat` | Claude SSE streaming + Tool-based RAG |
| conversations | `POST /conversations` | 创建对话 |
| | `GET /conversations` | 对话列表 |
| | `GET /conversations/{id}` | 对话详情 |
| | `DELETE /conversations/{id}` | 删除对话 |
| progress | `POST /progress` | 添加书目 |
| | `GET /progress` | 书目列表 |
| | `GET /progress/{id}` | 书目详情 |
| | `PUT /progress/{id}` | 更新书目 |
| | `DELETE /progress/{id}` | 删除书目 |

## License

MIT

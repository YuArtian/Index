# Index - 个人学习助手

RAG 知识库 + Claude Chat + 学习进度追踪。

## 快速启动

```bash
docker compose up -d db                                    # 1. 数据库 (:5432)
cd apps/api && source .venv/bin/activate && python main.py  # 2. 后端 (:8000)
cd apps/web && pnpm dev                                     # 3. 前端 (:5173)
```

或者用 Makefile: `make db`, `make api`, `make web`

## 项目结构

```
Index/
├── apps/
│   ├── api/                    # FastAPI 后端 (Python 3.13)
│   │   ├── main.py             # 入口
│   │   └── src/
│   │       ├── config.py       # pydantic-settings (.env + __ 分隔符)
│   │       ├── database.py     # SQLAlchemy async engine
│   │       ├── models/         # ORM: Document, Chunk, Conversation, Message, LearningItem, Chapter
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
│           ├── components/     # layout/ (Sidebar, AppLayout), chat/ (MessageList, ChatInput, SourceList)
│           ├── stores/         # Zustand + Immer (chat.ts)
│           ├── api/            # chat.ts, knowledge.ts, progress.ts
│           └── service/        # request.ts (Axios), sse.ts (SSE 流式解析)
│
├── infra/db/init.sql           # 6 张表 + pgvector 索引
├── docker-compose.yml
├── .env                        # 运行时配置 (不入版本控制)
└── .env.example                # 配置模板
```

## 技术栈

| 层 | 选择 |
|---|---|
| 后端 | FastAPI + SQLAlchemy 2.0 async + pgvector |
| 数据库 | PostgreSQL 17 + pgvector (Docker) |
| AI Chat | anthropic SDK (Claude Sonnet, Tool Use for RAG) |
| Embedding | 多 provider: Voyage AI / OpenAI / SiliconFlow / Local |
| 前端 | React 19 + Vite + TypeScript + TailwindCSS 4 |
| 状态管理 | Zustand + Immer |
| HTTP | Axios (拦截器) + SSE (fetch streaming) |

## 环境变量 (.env)

```bash
DATABASE__URL=postgresql+asyncpg://postgres:postgres@localhost:5432/index

# Embedding: "voyage" | "openai" | "siliconflow" | "local"
EMBEDDING__PROVIDER=voyage
EMBEDDING__API_KEY=pa-xxxx
EMBEDDING__BASE_URL=https://api.voyageai.com/v1
EMBEDDING__MODEL=voyage-3.5

# Claude Chat
ANTHROPIC_API_KEY=sk-ant-xxxx

CHUNK_SIZE=500
CHUNK_OVERLAP=50
CORS_ORIGINS=["http://localhost:5173"]
```

## 数据库 (6 张表)

| 表 | 用途 | 关键字段 |
|---|---|---|
| documents | 文档元数据 | status (uploading→parsing→indexing→ready→error) |
| chunks | 文档片段 + 向量 | embedding vector(1024), HNSW 索引 |
| conversations | 对话 | title, timestamps |
| messages | 消息 | role, content, input/output_tokens |
| learning_items | 书目 | status (reading/completed), 进度统计 |
| chapters | 章节 | status (pending/completed) |

## API 端点 (16 个)

| 路由 | 端点 | 说明 |
|---|---|---|
| knowledge | `GET /` | 健康检查 + 统计 |
| | `POST /index` | 索引文档 |
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
| | `GET /progress/{id}` | 书目详情 + 章节 |
| | `PUT /progress/{id}` | 更新书目 |
| | `DELETE /progress/{id}` | 删除书目 |
| | `PUT /progress/{id}/chapters/{ch_id}` | 更新章节状态 |

## 架构模式

### 后端

- **Provider 模式**: embedding/storage/parser 均可插拔替换
- **工厂函数**: `create_embedding_provider()`, `create_parser()`, router 的 `init_router(service)`
- **Lifespan**: 启动时初始化 provider → service → router，关闭时清理
- **SSE 流式**: Chat 使用 Server-Sent Events，事件类型: text / source / error / done
- **Tool Use RAG**: Claude 自主决定是否调用 `search_knowledge` 工具搜索知识库

### 前端

- **Zustand + Immer**: chat store 管理对话状态，乐观更新
- **SSE 消费**: `service/sse.ts` 解析流式响应，支持 AbortController 取消
- **懒加载**: 页面组件 lazy import + Suspense

## 开发约定

- Python: 类型注解, async/await, snake_case, loguru 日志
- TypeScript: 严格模式, @ 路径别名, 接口定义
- ORM: 关系用 back_populates, CASCADE 删除, DateTime(timezone=True)
- 样式: TailwindCSS utilities, clsx + tailwind-merge

## 当前进度

- [x] Phase 1: Monorepo 骨架 + 数据库
- [x] Phase 2: 后端 (pgvector, chat, progress, 16 endpoints)
- [x] Phase 3: 前端骨架 + Chat 页面
- [x] Phase 4: 知识库 + 学习进度前端
- [ ] Phase 5: 打磨 (错误处理, Loading 状态, RAG 参数调优)

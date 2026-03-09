# Index - 个人学习助手

个人"记忆宫殿"——将学过的资料（PDF/TXT/MD/图片/电子书）通过 AI 整理成可视化、可交互的知识网络。

核心能力：RAG 知识库 + Claude Chat + 学习进度追踪 + **知识图谱**。

## 快速启动

```bash
docker compose up -d db neo4j                               # 1. 数据库 (:5432) + Neo4j (:7474/:7687)
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
│   │       ├── models/         # ORM: Document, Chunk, Conversation, Message, LearningItem
│   │       ├── api/
│   │       │   ├── app.py      # 工厂函数 (lifespan + CORS + 服务注入)
│   │       │   ├── models.py   # Pydantic 请求/响应模型
│   │       │   └── routers/    # knowledge, chat, conversations, progress, graph
│   │       ├── services/       # 业务逻辑: Knowledge, Search, Chat, Progress, Graph
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
| 知识图谱 | Neo4j 5 + GDS plugin (Docker) |
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

# Neo4j
NEO4J__URI=bolt://localhost:7687
NEO4J__USER=neo4j
NEO4J__PASSWORD=neo4j_password
```

## 数据库 (5 张表 + Neo4j 图)

| 表 | 用途 | 关键字段 |
|---|---|---|
| documents | 文档元数据 | status (uploading→parsing→indexing→ready→error) |
| chunks | 文档片段 + 向量 | embedding vector(1024), HNSW 索引 |
| conversations | 对话 | title, timestamps |
| messages | 消息 | role, content, input/output_tokens |
| learning_items | 书目 | progress (0-100%), document_id FK, status (reading/completed) |

### Neo4j 知识图谱

| 节点/关系 | 用途 | 关键属性 |
|---|---|---|
| (:Concept) | 知识概念节点 | name (UNIQUE), category, description |
| [:RELATES_TO] | 概念间关系 | type (使用了/属于/包含...), weight, doc_ids[], chunk_ids[] |

- category 枚举: 技术/概念/工具/语言/框架/算法/设计模式/原理/人物/其他
- weight: 同一关系在多个文档出现时累加
- doc_ids/chunk_ids: 溯源到原文

## API 端点 (18 个)

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
| progress | `POST /progress` | 添加书目 (可关联 document_id) |
| | `GET /progress` | 书目列表 |
| | `GET /progress/{id}` | 书目详情 |
| | `PUT /progress/{id}` | 更新书目 (含 progress 百分比) |
| | `DELETE /progress/{id}` | 删除书目 |
| graph | `GET /graph` | 全图 (nodes + edges, 供可视化) |
| | `GET /graph/stats` | 概念数 + 关系数 |
| | `GET /graph/search?q=xxx` | 搜索概念 |
| | `GET /graph/neighbors/{name}` | N 跳关联查询 |

## 架构模式

### 后端

- **Provider 模式**: embedding/storage/parser 均可插拔替换
- **工厂函数**: `create_embedding_provider()`, `create_parser()`, router 的 `init_router(service)`
- **Lifespan**: 启动时初始化 provider → service → router，关闭时清理
- **SSE 流式**: Chat 使用 Server-Sent Events，事件类型: text / source / error / done
- **Tool Use RAG**: Claude 自主决定是否调用 `search_knowledge` 工具搜索知识库
- **知识图谱**: 文档索引时 Claude 自动提取概念+关系 → 写入 Neo4j，删除时自动清理

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
- [x] Phase 2: 后端 (pgvector, chat, progress, 18 endpoints)
- [x] Phase 3: 前端骨架 + Chat 页面
- [x] Phase 4: 知识库 + 学习进度前端
- [x] Phase 5a: 知识图谱后端 (Neo4j + GraphService + 4 endpoints)
- [ ] **Phase 5b: 知识图谱前端 (/graph 页面)** ← 下一步
- [ ] Phase 6: 打磨 (错误处理, Loading 状态, RAG 参数调优)
- [ ] Phase 7: 3D 记忆宫殿 (/palace)

## 下一步: /graph 前端页面

### 技术选型
- react-force-graph-3d: 默认俯视角(看起来像 2D)，按钮切换 3D 视角
- 同一个组件，通过 cameraPosition() 动画切换，过渡平滑

### 页面布局
- 顶栏: 搜索框 + [2D][3D] 切换 + category 筛选
- 左侧主画布: 力导向图 (节点=概念, 边=关系, 大小=连接数, 颜色=category)
- 右侧详情面板: 概念名/类别/描述/连接数/关联原文
- 底栏: 概念数/关系数/文档数 统计

### 交互
- 点击节点 → 右侧详情
- 双击节点 → 聚焦模式 (以该节点为中心展开)
- 搜索 → 高亮并飞到目标节点
- 筛选 → 按 category 过滤
- [3D] → 相机从俯视动画到 45° 斜视角，启用旋转

### 未来: /palace (3D 记忆宫殿)
- React Three Fiber (@react-three/fiber + @react-three/drei)
- 3D 书架(书脊=书名)、知识节点漂浮在空间中
- 点击书 → 飞进去看内容; 点击概念 → 关联书和笔记浮现

# Index

本地知识库语义检索系统 - MVP 版本

## 功能

- 📄 文档索引：将文本分块并存储为向量
- 🔍 语义检索：基于相似度搜索相关内容
- 💾 本地存储：使用 ChromaDB 持久化数据

## 快速开始

### 1. 安装依赖

```bash
cd Index
uv sync
```

### 2. 配置 API Key

复制配置文件并填入你的 API Key：

```bash
cp env.example .env
```

编辑 `.env` 文件：

```bash
# 推荐：硅基流动（有免费额度）
SILICONFLOW_API_KEY=your_api_key_here

# 或者：OpenAI
# OPENAI_API_KEY=your_api_key_here
```

> 💡 如果不配置 API Key，将自动使用本地模型（需要额外安装 `sentence-transformers`）

### 3. 启动服务

```bash
uv run python main.py
```

服务启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/

## API 接口

### 索引文档

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{"content": "这是要索引的文本内容", "source": "test"}'
```

### 搜索

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "搜索关键词", "top_k": 5}'
```

### 查看所有文档

```bash
curl http://localhost:8000/documents
```

### 删除文档

```bash
curl -X DELETE http://localhost:8000/documents/{doc_id}
```

## 技术栈

- **Web 框架**: FastAPI
- **向量数据库**: ChromaDB（嵌入式）
- **Embedding**: 硅基流动 API / OpenAI / 本地模型

## 目录结构

```
Index/
├── main.py           # 主程序（单文件 MVP）
├── data/             # ChromaDB 数据（自动创建）
│   └── chroma/
├── pyproject.toml    # 依赖配置
├── env.example       # 环境变量示例
└── README.md
```

## License

MIT

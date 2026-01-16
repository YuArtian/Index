# Index - 本地知识库

一个轻量级但功能完整的本地知识库系统，支持语义搜索。

## 特性

- 🔍 **语义搜索** - 基于向量嵌入的相似度搜索
- 🔌 **可插拔架构** - Provider 模式，易于扩展
- 📄 **多格式支持** - 支持纯文本和 Markdown
- 🏠 **本地优先** - 默认使用本地模型，无需 API

## 架构

```
src/
├── config.py              # 配置管理
├── providers/             # Provider 层 (可插拔组件)
│   ├── embedding/         # Embedding 服务
│   ├── storage/           # 存储服务
│   └── parser/            # 文档解析
├── services/              # Service 层 (业务逻辑)
│   ├── knowledge.py       # 知识库管理
│   └── search.py          # 搜索服务
└── api/                   # API 层
    ├── app.py             # FastAPI 应用
    ├── routes.py          # 路由定义
    └── models.py          # 数据模型
```

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv (推荐)
uv venv
source .venv/bin/activate
uv pip install -e .

# 如果需要本地 Embedding 模型
uv pip install -e ".[local]"
```

### 2. 配置环境变量

```bash
cp env.example .env
# 编辑 .env 设置 API Key (可选，不设置则使用本地模型)
```

### 3. 启动服务

```bash
python main.py
# 或
uvicorn main:app --reload
```

### 4. 访问 API

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/

## API 接口

### 索引文档

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你的文档内容",
    "source": "来源标识",
    "file_type": "text"
  }'
```

### 搜索

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "搜索关键词",
    "top_k": 5
  }'
```

### 查看文档列表

```bash
curl http://localhost:8000/documents
```

### 删除文档

```bash
curl -X DELETE http://localhost:8000/documents/{doc_id}
```

## 配置选项

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `SILICONFLOW_API_KEY` | 硅基流动 API Key | - |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `EMBEDDING_MODEL` | Embedding 模型 | 自动选择 |
| `STORAGE_PROVIDER` | 存储后端 | chroma |
| `STORAGE_PATH` | 存储路径 | ./data/chroma |
| `CHUNK_SIZE` | 分块大小 | 500 |
| `CHUNK_OVERLAP` | 分块重叠 | 50 |

## Provider 扩展

### 添加新的 Embedding Provider

```python
# src/providers/embedding/custom.py
from .base import EmbeddingProvider

class CustomEmbeddingProvider(EmbeddingProvider):
    async def embed(self, text: str) -> list[float]:
        # 实现你的逻辑
        pass
```

### 添加新的 Storage Provider

```python
# src/providers/storage/custom.py
from .base import StorageProvider

class CustomStorageProvider(StorageProvider):
    def add(self, ids, documents, embeddings, metadatas):
        # 实现你的逻辑
        pass
```

## License

MIT

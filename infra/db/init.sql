-- Index 数据库初始化
-- 由 docker-entrypoint-initdb.d 自动执行

CREATE EXTENSION IF NOT EXISTS vector;

-- 文档（chunks 的父表，追踪文件处理状态）
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    source TEXT,
    content_type TEXT,
    status TEXT DEFAULT 'uploading',
    error_message TEXT,
    chunk_count INTEGER DEFAULT 0,
    file_size INTEGER,
    file_path TEXT,                  -- 原始文件存储路径
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_documents_status ON documents (status);

-- 知识库 chunks（向量 + 内容）
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1024),
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    source TEXT,
    chunk_index INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ix_chunks_doc_id ON chunks (doc_id);

-- 学习进度
CREATE TABLE learning_items (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    type TEXT DEFAULT 'book',
    progress INTEGER DEFAULT 0,          -- 0-100 百分比
    status TEXT DEFAULT 'reading',       -- reading / completed
    notes TEXT,
    document_id TEXT REFERENCES documents(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_learning_items_status ON learning_items (status);
CREATE INDEX ix_learning_items_document_id ON learning_items (document_id);

-- 对话历史
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_conversations_updated_at ON conversations (updated_at DESC);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_messages_conversation_id ON messages (conversation_id);

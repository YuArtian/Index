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
    total_chapters INTEGER DEFAULT 0,
    completed_chapters INTEGER DEFAULT 0,
    status TEXT DEFAULT 'reading',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_learning_items_status ON learning_items (status);

CREATE TABLE chapters (
    id TEXT PRIMARY KEY,
    learning_item_id TEXT REFERENCES learning_items(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    chapter_index INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    completed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_chapters_learning_item_id ON chapters (learning_item_id);

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

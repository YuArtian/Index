import { useEffect, useState } from 'react'
import { Upload, Trash2, FileText } from 'lucide-react'
import { knowledgeApi } from '@/api/knowledge'

interface Document {
  id: string
  filename: string
  source: string
  status: string
  chunk_count: number
  created_at: string
}

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [content, setContent] = useState('')
  const [source, setSource] = useState('')
  const [uploading, setUploading] = useState(false)

  const loadDocuments = async () => {
    const data = await knowledgeApi.listDocuments()
    setDocuments(data.documents)
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  const handleUpload = async () => {
    if (!content.trim()) return
    setUploading(true)
    try {
      const fileType = source.endsWith('.md') ? 'markdown' : 'text'
      await knowledgeApi.indexDocument(content, source || 'manual', fileType)
      setContent('')
      setSource('')
      await loadDocuments()
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (docId: string) => {
    await knowledgeApi.deleteDocument(docId)
    await loadDocuments()
  }

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      ready: 'bg-green-100 text-green-700',
      indexing: 'bg-yellow-100 text-yellow-700',
      parsing: 'bg-blue-100 text-blue-700',
      error: 'bg-red-100 text-red-700',
      uploading: 'bg-gray-100 text-gray-700',
    }
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs ${colors[status] || colors.uploading}`}>
        {status}
      </span>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-6">知识库</h2>

      {/* Upload form */}
      <div className="bg-gray-50 rounded-xl p-4 mb-6 border border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-3">添加文档</h3>
        <input
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder="来源名称 (如: notes.md)"
          className="w-full mb-2 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="粘贴文档内容..."
          rows={4}
          className="w-full mb-2 px-3 py-2 text-sm border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleUpload}
          disabled={!content.trim() || uploading}
          className="flex items-center gap-1 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          <Upload size={16} />
          {uploading ? '索引中...' : '索引文档'}
        </button>
      </div>

      {/* Document list */}
      <div className="space-y-2">
        {documents.length === 0 && (
          <p className="text-gray-400 text-sm text-center py-8">暂无文档</p>
        )}
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="flex items-center gap-3 p-3 bg-white rounded-xl border border-gray-200 hover:border-gray-300 transition-colors"
          >
            <FileText size={18} className="text-gray-400 shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
              <p className="text-xs text-gray-500">{doc.chunk_count} chunks</p>
            </div>
            {statusBadge(doc.status)}
            <button
              onClick={() => handleDelete(doc.id)}
              className="p-1 text-gray-400 hover:text-red-500 transition-colors"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

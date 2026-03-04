import { useEffect, useRef, useState } from 'react'
import { Upload, Trash2, FileText, FolderOpen } from 'lucide-react'
import { knowledgeApi } from '@/api/knowledge'

interface Document {
  id: string
  filename: string
  source: string
  status: string
  chunk_count: number
  created_at: string
}

// Accepted file extensions for the file picker
const ACCEPTED_EXTENSIONS = [
  '.txt', '.md', '.markdown',
  '.pdf',
  '.docx',
  '.csv', '.xlsx', '.xls',
  '.ipynb',
  '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif',
].join(',')

const FILE_TYPE_GROUPS = [
  { label: '文本', exts: '.txt / .md' },
  { label: 'PDF', exts: '.pdf' },
  { label: 'Word', exts: '.docx' },
  { label: '表格', exts: '.csv / .xlsx / .xls' },
  { label: 'Notebook', exts: '.ipynb' },
  { label: '图片', exts: '.jpg / .png / .gif / .webp / .bmp / .tiff' },
]

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [content, setContent] = useState('')
  const [source, setSource] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [highQuality, setHighQuality] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const loadDocuments = async () => {
    const data = await knowledgeApi.listDocuments()
    setDocuments(data.documents)
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  // Text paste upload
  const handleUpload = async () => {
    if (!content.trim()) return
    setUploading(true)
    setUploadError('')
    try {
      const fileType = source.endsWith('.md') || source.endsWith('.markdown') ? 'markdown' : 'text'
      await knowledgeApi.indexDocument(content, source || 'manual', fileType)
      setContent('')
      setSource('')
      await loadDocuments()
    } catch {
      setUploadError('索引失败，请检查内容后重试')
    } finally {
      setUploading(false)
    }
  }

  // File picker: just record the selection, don't upload yet
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null
    setSelectedFile(file)
    setUploadError('')
    // Reset high quality if switching away from PDF
    if (file && !file.name.toLowerCase().endsWith('.pdf')) {
      setHighQuality(false)
    }
  }

  // Confirm upload
  const handleFileUpload = async () => {
    if (!selectedFile) return
    setUploading(true)
    setUploadError('')
    try {
      await knowledgeApi.uploadFile(selectedFile, highQuality)
      setSelectedFile(null)
      setHighQuality(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
      await loadDocuments()
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? '上传失败，请检查文件格式'
      setUploadError(msg)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (docId: string) => {
    await knowledgeApi.deleteDocument(docId)
    await loadDocuments()
  }

  const isPdf = selectedFile?.name.toLowerCase().endsWith('.pdf') ?? false

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      ready: 'bg-green-100 text-green-700',
      indexing: 'bg-yellow-100 text-yellow-700',
      parsing: 'bg-blue-100 text-blue-700',
      error: 'bg-red-100 text-red-700',
      uploading: 'bg-gray-100 text-gray-700',
    }
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs ${colors[status] ?? colors.uploading}`}>
        {status}
      </span>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-6">知识库</h2>

      {/* Upload panel */}
      <div className="bg-gray-50 rounded-xl p-4 mb-4 border border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-3">添加文档</h3>

        {/* File upload button */}
        <div className="mb-3">
          <div className="flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_EXTENSIONS}
              className="hidden"
              onChange={handleFileChange}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <FolderOpen size={16} className="text-gray-500" />
              {selectedFile ? selectedFile.name : '选择文件'}
            </button>
            {selectedFile && (
              <button
                onClick={handleFileUpload}
                disabled={uploading}
                className="flex items-center gap-1 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                <Upload size={16} />
                {uploading ? '处理中...' : '上传'}
              </button>
            )}
          </div>

          {/* High quality toggle — only for PDF */}
          {isPdf && (
            <label className="flex items-center gap-2 mt-2 cursor-pointer w-fit">
              <input
                type="checkbox"
                checked={highQuality}
                onChange={(e) => setHighQuality(e.target.checked)}
                className="w-3.5 h-3.5 accent-blue-600"
              />
              <span className="text-xs text-gray-600">
                高质量模式（Claude Vision 逐页识别，保留公式和图表，速度较慢）
              </span>
            </label>
          )}
        </div>

        <div className="flex items-center gap-2 mb-3">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-xs text-gray-400">或直接粘贴内容</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>

        {/* Text paste */}
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

        {uploadError && (
          <p className="mt-2 text-xs text-red-600">{uploadError}</p>
        )}
      </div>

      {/* Supported type tags */}
      <div className="flex flex-wrap gap-1 mb-5">
        {FILE_TYPE_GROUPS.map((g) => (
          <span
            key={g.label}
            title={g.exts}
            className="px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded-full cursor-default"
          >
            {g.label}
          </span>
        ))}
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

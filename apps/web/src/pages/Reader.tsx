import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, MessageSquare, Loader2 } from 'lucide-react'
import { knowledgeApi } from '@/api/knowledge'
import { progressApi } from '@/api/progress'
import PdfViewer from '@/components/PdfViewer'

interface LearningItem {
  id: string
  title: string
  author: string | null
  progress: number
  status: string
  document_id: string | null
  filename: string | null
}

function isPdf(filename: string | null) {
  return filename?.toLowerCase().endsWith('.pdf') ?? false
}

export default function ReaderPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [item, setItem] = useState<LearningItem | null>(null)
  const [textContent, setTextContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedText, setSelectedText] = useState<string | null>(null)
  const [selectionPos, setSelectionPos] = useState<{ x: number; y: number } | null>(null)
  const textContainerRef = useRef<HTMLDivElement>(null)
  const progressTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!id) return
    const load = async () => {
      try {
        const data = await progressApi.getItem(id)
        setItem(data)
        if (!data.document_id) {
          setError('该书籍没有关联文件')
          return
        }
        if (!isPdf(data.filename)) {
          const fileUrl = knowledgeApi.getDocumentFileUrl(data.document_id)
          const res = await fetch(fileUrl)
          if (!res.ok) throw new Error('File not found')
          setTextContent(await res.text())
        }
      } catch {
        setError('加载失败')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  // Debounced progress save
  const saveProgress = useCallback(
    (progress: number) => {
      if (!id) return
      if (progressTimerRef.current) clearTimeout(progressTimerRef.current)
      progressTimerRef.current = setTimeout(() => {
        progressApi.updateItem(id, { progress })
      }, 1000)
    },
    [id],
  )

  // PDF page change → auto progress
  const handlePdfPageChange = useCallback(
    (page: number, total: number) => {
      const progress = Math.round((page / total) * 100)
      setItem((prev) => (prev ? { ...prev, progress } : prev))
      saveProgress(progress)
    },
    [saveProgress],
  )

  // Text scroll → auto progress
  const handleTextScroll = useCallback(() => {
    const el = textContainerRef.current
    if (!el) return
    const progress = Math.round((el.scrollTop / (el.scrollHeight - el.clientHeight)) * 100)
    const clamped = Math.min(100, Math.max(0, progress))
    setItem((prev) => (prev ? { ...prev, progress: clamped } : prev))
    saveProgress(clamped)
  }, [saveProgress])

  // Text selection handler (for non-PDF)
  const handleTextMouseUp = useCallback(() => {
    const selection = window.getSelection()
    const text = selection?.toString().trim()
    if (text) {
      setSelectedText(text)
      const range = selection!.getRangeAt(0)
      const rect = range.getBoundingClientRect()
      setSelectionPos({ x: rect.left + rect.width / 2, y: rect.top - 10 })
    } else {
      setSelectedText(null)
      setSelectionPos(null)
    }
  }, [])

  // PDF text selection
  const handlePdfTextSelect = useCallback((text: string) => {
    if (text) {
      setSelectedText(text)
      const selection = window.getSelection()
      if (selection && selection.rangeCount > 0) {
        const range = selection.getRangeAt(0)
        const rect = range.getBoundingClientRect()
        setSelectionPos({ x: rect.left + rect.width / 2, y: rect.top - 10 })
      }
    } else {
      setSelectedText(null)
      setSelectionPos(null)
    }
  }, [])

  const askAboutSelection = () => {
    if (selectedText && id) {
      navigate(`/chat?book=${id}&q=${encodeURIComponent(selectedText)}`)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <Loader2 size={24} className="animate-spin" />
      </div>
    )
  }

  if (error || !item) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-3">
        <p>{error || '未找到'}</p>
        <button onClick={() => navigate('/')} className="text-sm text-blue-600 hover:underline">
          返回书架
        </button>
      </div>
    )
  }

  const fileUrl = item.document_id ? knowledgeApi.getDocumentFileUrl(item.document_id) : null

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-gray-200 bg-white shrink-0">
        <button
          onClick={() => navigate('/')}
          className="p-1.5 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="text-sm font-medium text-gray-900 truncate">{item.title}</h1>
          {item.author && <p className="text-xs text-gray-500">{item.author}</p>}
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span className="text-xs text-gray-500">{item.progress}%</span>
          <div className="w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-300"
              style={{ width: `${item.progress}%` }}
            />
          </div>
          <button
            onClick={() => navigate(`/chat?book=${id}`)}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <MessageSquare size={14} />
            提问
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 relative">
        {isPdf(item.filename) && fileUrl ? (
          <PdfViewer
            url={fileUrl}
            initialProgress={item.progress}
            onPageChange={handlePdfPageChange}
            onTextSelect={handlePdfTextSelect}
          />
        ) : (
          <div
            ref={textContainerRef}
            className="absolute inset-0 overflow-y-auto"
            onScroll={handleTextScroll}
            onMouseUp={handleTextMouseUp}
          >
            <div className="max-w-3xl mx-auto px-8 py-10">
              <article className="prose prose-gray max-w-none whitespace-pre-wrap text-[15px] leading-relaxed">
                {textContent}
              </article>
            </div>
          </div>
        )}

        {/* Floating selection action */}
        {selectedText && selectionPos && (
          <button
            onClick={askAboutSelection}
            className="fixed z-50 flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg shadow-lg hover:bg-blue-700 transition-colors"
            style={{
              left: selectionPos.x,
              top: selectionPos.y,
              transform: 'translate(-50%, -100%)',
            }}
          >
            <MessageSquare size={14} />
            提问
          </button>
        )}
      </div>
    </div>
  )
}

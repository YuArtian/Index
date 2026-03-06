import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, MessageSquare, Loader2, List, ChevronRight, ChevronsDownUp, ChevronsUpDown, X } from 'lucide-react'
import { knowledgeApi } from '@/api/knowledge'
import { progressApi, type LearningItem } from '@/api/progress'
import PdfViewer, { type OutlineItem, type PdfViewerHandle } from '@/components/PdfViewer'

function isPdf(filename: string | null) {
  return filename?.toLowerCase().endsWith('.pdf') ?? false
}

interface TextHeading {
  title: string
  level: number
  offset: number
}

function parseTextHeadings(text: string): TextHeading[] {
  const lines = text.split('\n')
  const headings: TextHeading[] = []
  let offset = 0
  for (const line of lines) {
    const trimmed = line.trim()
    // Detect markdown-style headings or lines that look like chapter titles
    const mdMatch = trimmed.match(/^(#{1,3})\s+(.+)/)
    if (mdMatch) {
      headings.push({ title: mdMatch[2], level: mdMatch[1].length, offset })
    } else if (
      trimmed.length > 0 &&
      trimmed.length < 60 &&
      /^(第[一二三四五六七八九十百千\d]+[章节篇回]|chapter\s+\d+|part\s+\d+)/i.test(trimmed)
    ) {
      headings.push({ title: trimmed, level: 1, offset })
    }
    offset += line.length + 1
  }
  return headings
}

// Recursive outline item component
function OutlineEntry({
  item,
  depth,
  onSelect,
  expandAll,
  onManualToggle,
}: {
  item: OutlineItem
  depth: number
  onSelect: (dest: unknown) => void
  expandAll: boolean | null
  onManualToggle: () => void
}) {
  const [localExpanded, setLocalExpanded] = useState(expandAll !== null ? expandAll : depth < 1)
  const [lastExpandAll, setLastExpandAll] = useState(expandAll)
  const hasChildren = item.items && item.items.length > 0

  // Sync local state when expandAll changes (derived state pattern)
  if (expandAll !== lastExpandAll) {
    setLastExpandAll(expandAll)
    if (expandAll !== null) setLocalExpanded(expandAll)
  }

  return (
    <div>
      <button
        onClick={() => {
          onSelect(item.dest)
          if (hasChildren) {
            setLocalExpanded((e) => !e)
            onManualToggle()
          }
        }}
        className="flex items-center gap-1 w-full text-left px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded transition-colors"
        style={{ paddingLeft: `${12 + depth * 16}px` }}
        title={item.title}
      >
        {hasChildren && (
          <ChevronRight
            size={14}
            className={`shrink-0 text-gray-400 transition-transform ${localExpanded ? 'rotate-90' : ''}`}
          />
        )}
        <span className="truncate">{item.title}</span>
      </button>
      {hasChildren && localExpanded && (
        <div>
          {item.items.map((child, i) => (
            <OutlineEntry key={i} item={child} depth={depth + 1} onSelect={onSelect} expandAll={expandAll} onManualToggle={onManualToggle} />
          ))}
        </div>
      )}
    </div>
  )
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
  const pdfViewerRef = useRef<PdfViewerHandle>(null)

  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [pdfOutline, setPdfOutline] = useState<OutlineItem[]>([])
  const [textHeadings, setTextHeadings] = useState<TextHeading[]>([])
  const [outlineExpandAll, setOutlineExpandAll] = useState<boolean | null>(null)

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
          const text = await res.text()
          setTextContent(text)
          setTextHeadings(parseTextHeadings(text))
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

  const handleOutlineSelect = (dest: unknown) => {
    pdfViewerRef.current?.goToDestination(dest)
  }

  const handleTextHeadingClick = (heading: TextHeading) => {
    const el = textContainerRef.current
    if (!el || textContent === null) return
    // Find the position ratio and scroll to it
    const ratio = heading.offset / textContent.length
    el.scrollTop = ratio * (el.scrollHeight - el.clientHeight)
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
        <button
          onClick={() => setSidebarOpen((v) => !v)}
          className={`p-1.5 rounded-lg transition-colors ${
            sidebarOpen ? 'text-blue-600 bg-blue-50' : 'text-gray-500 hover:bg-gray-100'
          }`}
          title="章节目录"
        >
          <List size={18} />
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

      {/* Content area with sidebar */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Chapter Sidebar */}
        {sidebarOpen && (
          <div className="w-72 shrink-0 border-r border-gray-200 bg-white flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
              <h2 className="text-sm font-medium text-gray-900">目录</h2>
              <div className="flex items-center gap-1">
                {isPdf(item.filename) && pdfOutline.length > 0 && (
                  <button
                    onClick={() =>
                      setOutlineExpandAll((v) => (v === null || !v ? true : false))
                    }
                    className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
                    title={outlineExpandAll ? '全部收起' : '全部展开'}
                  >
                    {outlineExpandAll ? <ChevronsDownUp size={16} /> : <ChevronsUpDown size={16} />}
                  </button>
                )}
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto py-2">
              {isPdf(item.filename) && pdfOutline.length > 0 ? (
                pdfOutline.map((entry, i) => (
                  <OutlineEntry key={i} item={entry} depth={0} onSelect={handleOutlineSelect} expandAll={outlineExpandAll} onManualToggle={() => setOutlineExpandAll(null)} />
                ))
              ) : textHeadings.length > 0 ? (
                textHeadings.map((heading, i) => (
                  <button
                    key={i}
                    onClick={() => handleTextHeadingClick(heading)}
                    className="block w-full text-left px-4 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded transition-colors truncate"
                    style={{ paddingLeft: `${16 + (heading.level - 1) * 16}px` }}
                    title={heading.title}
                  >
                    {heading.title}
                  </button>
                ))
              ) : (
                <p className="px-4 py-3 text-sm text-gray-400">暂无章节信息</p>
              )}
            </div>
          </div>
        )}

        {/* Main content */}
        <div className="flex-1 relative">
          {isPdf(item.filename) && fileUrl ? (
            <PdfViewer
              ref={pdfViewerRef}
              url={fileUrl}
              initialProgress={item.progress}
              onPageChange={handlePdfPageChange}
              onTextSelect={handlePdfTextSelect}
              onOutlineLoaded={setPdfOutline}
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
    </div>
  )
}

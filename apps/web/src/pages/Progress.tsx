import { useEffect, useState } from 'react'
import { Plus, Trash2, BookOpen, Check } from 'lucide-react'
import { progressApi } from '@/api/progress'

interface LearningItem {
  id: string
  title: string
  author: string | null
  total_chapters: number
  completed_chapters: number
  status: string
}

interface Chapter {
  id: string
  title: string
  chapter_index: number
  status: string
}

export default function ProgressPage() {
  const [items, setItems] = useState<LearningItem[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [showAdd, setShowAdd] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newAuthor, setNewAuthor] = useState('')
  const [newChapters, setNewChapters] = useState('')

  const loadItems = async () => {
    const data = await progressApi.listItems()
    setItems(data.items)
  }

  const loadChapters = async (id: string) => {
    const data = await progressApi.getItem(id)
    setChapters(data.chapters)
  }

  useEffect(() => {
    loadItems()
  }, [])

  const handleSelect = (id: string) => {
    setSelectedId(id)
    loadChapters(id)
  }

  const handleAdd = async () => {
    if (!newTitle.trim()) return
    const chapList = newChapters
      .split('\n')
      .map((c) => c.trim())
      .filter(Boolean)
    await progressApi.createItem({
      title: newTitle,
      author: newAuthor || undefined,
      chapters: chapList.length > 0 ? chapList : undefined,
    })
    setNewTitle('')
    setNewAuthor('')
    setNewChapters('')
    setShowAdd(false)
    await loadItems()
  }

  const handleToggleChapter = async (chapterId: string, currentStatus: string) => {
    if (!selectedId) return
    const newStatus = currentStatus === 'completed' ? 'pending' : 'completed'
    await progressApi.updateChapter(selectedId, chapterId, { status: newStatus })
    await loadChapters(selectedId)
    await loadItems()
  }

  const handleDelete = async (id: string) => {
    await progressApi.deleteItem(id)
    if (selectedId === id) {
      setSelectedId(null)
      setChapters([])
    }
    await loadItems()
  }

  return (
    <div className="flex h-full">
      {/* Item list */}
      <div className="w-72 border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">学习进度</h2>
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="p-1.5 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Plus size={18} />
          </button>
        </div>

        {showAdd && (
          <div className="p-3 border-b border-gray-200 bg-gray-50 space-y-2">
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="书名"
              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              value={newAuthor}
              onChange={(e) => setNewAuthor(e.target.value)}
              placeholder="作者 (可选)"
              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <textarea
              value={newChapters}
              onChange={(e) => setNewChapters(e.target.value)}
              placeholder="章节列表 (每行一个)"
              rows={3}
              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleAdd}
              disabled={!newTitle.trim()}
              className="w-full px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
            >
              添加
            </button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {items.map((item) => {
            const pct =
              item.total_chapters > 0
                ? Math.round((item.completed_chapters / item.total_chapters) * 100)
                : 0
            return (
              <div
                key={item.id}
                onClick={() => handleSelect(item.id)}
                className={`group p-3 rounded-xl cursor-pointer transition-colors ${
                  selectedId === item.id
                    ? 'bg-blue-50 border border-blue-200'
                    : 'hover:bg-gray-50 border border-transparent'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">{item.title}</p>
                    {item.author && (
                      <p className="text-xs text-gray-500">{item.author}</p>
                    )}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(item.id)
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
                {item.total_chapters > 0 && (
                  <div className="mt-2">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>
                        {item.completed_chapters}/{item.total_chapters}
                      </span>
                      <span>{pct}%</span>
                    </div>
                    <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Chapter detail */}
      <div className="flex-1 p-6 overflow-y-auto">
        {!selectedId ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <BookOpen size={48} className="mx-auto mb-2 opacity-50" />
              <p>选择一本书查看章节</p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {chapters.map((ch) => (
              <div
                key={ch.id}
                onClick={() => handleToggleChapter(ch.id, ch.status)}
                className="flex items-center gap-3 p-3 rounded-xl border border-gray-200 hover:border-gray-300 cursor-pointer transition-colors"
              >
                <div
                  className={`w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-colors ${
                    ch.status === 'completed'
                      ? 'bg-blue-600 border-blue-600'
                      : 'border-gray-300'
                  }`}
                >
                  {ch.status === 'completed' && <Check size={14} className="text-white" />}
                </div>
                <span
                  className={`text-sm ${
                    ch.status === 'completed' ? 'text-gray-400 line-through' : 'text-gray-900'
                  }`}
                >
                  {ch.title}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Plus, Trash2, BookOpen } from 'lucide-react'
import { progressApi } from '@/api/progress'

interface LearningItem {
  id: string
  title: string
  author: string | null
  progress: number
  status: string
}

export default function ProgressPage() {
  const [items, setItems] = useState<LearningItem[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedItem, setSelectedItem] = useState<LearningItem | null>(null)
  const [showAdd, setShowAdd] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newAuthor, setNewAuthor] = useState('')

  const loadItems = async () => {
    const data = await progressApi.listItems()
    setItems(data.items)
  }

  useEffect(() => {
    loadItems()
  }, [])

  const handleSelect = async (id: string) => {
    setSelectedId(id)
    const data = await progressApi.getItem(id)
    setSelectedItem(data)
  }

  const handleAdd = async () => {
    if (!newTitle.trim()) return
    await progressApi.createItem({
      title: newTitle,
      author: newAuthor || undefined,
    })
    setNewTitle('')
    setNewAuthor('')
    setShowAdd(false)
    await loadItems()
  }

  const handleProgressChange = async (value: number) => {
    if (!selectedId || !selectedItem) return
    setSelectedItem({ ...selectedItem, progress: value })
    await progressApi.updateItem(selectedId, { progress: value })
    await loadItems()
  }

  const handleDelete = async (id: string) => {
    await progressApi.deleteItem(id)
    if (selectedId === id) {
      setSelectedId(null)
      setSelectedItem(null)
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
          {items.map((item) => (
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
              <div className="mt-2">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>{item.status === 'completed' ? '已完成' : '阅读中'}</span>
                  <span>{item.progress}%</span>
                </div>
                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all"
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detail */}
      <div className="flex-1 p-6 overflow-y-auto">
        {!selectedItem ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <BookOpen size={48} className="mx-auto mb-2 opacity-50" />
              <p>选择一本书查看进度</p>
            </div>
          </div>
        ) : (
          <div className="max-w-md">
            <h2 className="text-xl font-bold text-gray-900">{selectedItem.title}</h2>
            {selectedItem.author && (
              <p className="text-sm text-gray-500 mt-1">{selectedItem.author}</p>
            )}
            <div className="mt-8">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                阅读进度: {selectedItem.progress}%
              </label>
              <input
                type="range"
                min={0}
                max={100}
                value={selectedItem.progress}
                onChange={(e) => handleProgressChange(Number(e.target.value))}
                className="w-full accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0%</span>
                <span>100%</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

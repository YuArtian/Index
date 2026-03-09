import { NavLink } from 'react-router-dom'
import { MessageSquare, BookOpen, Library, Bookmark, Share2 } from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', icon: BookOpen, label: '书架' },
  { to: '/chat', icon: MessageSquare, label: '对话' },
  { to: '/knowledge', icon: Library, label: '知识库' },
  { to: '/progress', icon: Bookmark, label: '阅读进度' },
  { to: '/graph', icon: Share2, label: '知识图谱' },
]

export function Sidebar() {
  return (
    <aside className="w-56 border-r border-gray-200 bg-gray-50 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-lg font-bold text-gray-900">Index</h1>
        <p className="text-xs text-gray-500">学习助手</p>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-100',
              )
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}

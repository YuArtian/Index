import { Outlet } from 'react-router-dom'
import { Suspense } from 'react'
import { Sidebar } from './Sidebar'

export function AppLayout() {
  return (
    <div className="flex h-screen bg-white">
      <Sidebar />
      <main className="flex-1 overflow-hidden">
        <Suspense
          fallback={
            <div className="flex items-center justify-center h-full text-gray-400">
              加载中...
            </div>
          }
        >
          <Outlet />
        </Suspense>
      </main>
    </div>
  )
}

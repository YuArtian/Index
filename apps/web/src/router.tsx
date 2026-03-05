import { createBrowserRouter } from 'react-router-dom'
import { lazy } from 'react'
import { AppLayout } from './components/layout/AppLayout'

const Bookshelf = lazy(() => import('./pages/Bookshelf'))
const Chat = lazy(() => import('./pages/Chat'))
const Knowledge = lazy(() => import('./pages/Knowledge'))
const Progress = lazy(() => import('./pages/Progress'))

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <Bookshelf /> },
      { path: '/chat', element: <Chat /> },
      { path: '/knowledge', element: <Knowledge /> },
      { path: '/progress', element: <Progress /> },
    ],
  },
])

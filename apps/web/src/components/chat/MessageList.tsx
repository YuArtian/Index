import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

interface Props {
  messages: Message[]
  isStreaming: boolean
}

export function MessageList({ messages, isStreaming }: Props) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full text-gray-400">
          <div className="text-center">
            <p className="text-lg">开始一段新对话</p>
            <p className="text-sm mt-1">输入问题，我会帮你从知识库中检索相关内容</p>
          </div>
        </div>
      )}
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={cn(
            'max-w-[80%] rounded-xl px-4 py-3',
            msg.role === 'user'
              ? 'ml-auto bg-blue-600 text-white'
              : 'mr-auto bg-gray-100 text-gray-900',
          )}
        >
          {msg.role === 'assistant' ? (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.content || (isStreaming ? '...' : '')}
              </ReactMarkdown>
            </div>
          ) : (
            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
          )}
        </div>
      ))}
    </div>
  )
}

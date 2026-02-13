import { useEffect, useRef } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { useChatStore } from '@/stores/chat'
import { MessageList } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { SourceList } from '@/components/chat/SourceList'
import { cn } from '@/lib/utils'

export default function ChatPage() {
  const {
    conversations,
    currentId,
    messages,
    sources,
    isStreaming,
    loadConversations,
    createConversation,
    loadConversation,
    sendMessage,
    stopStreaming,
    deleteConversation,
  } = useChatStore()

  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex h-full">
      {/* Conversation list sidebar */}
      <div className="w-56 border-r border-gray-200 flex flex-col bg-white">
        <div className="p-3 border-b border-gray-200">
          <button
            onClick={() => createConversation()}
            className="w-full flex items-center justify-center gap-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={16} />
            新对话
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={cn(
                'group flex items-center gap-1 px-3 py-2 rounded-lg text-sm cursor-pointer transition-colors',
                currentId === conv.id
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100',
              )}
              onClick={() => loadConversation(conv.id)}
            >
              <span className="flex-1 truncate">
                {conv.title || '新对话'}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  deleteConversation(conv.id)
                }}
                className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        <MessageList messages={messages} isStreaming={isStreaming} />
        <div ref={messagesEndRef} />
        <SourceList sources={sources} />
        <ChatInput
          onSend={sendMessage}
          onStop={stopStreaming}
          isStreaming={isStreaming}
        />
      </div>
    </div>
  )
}

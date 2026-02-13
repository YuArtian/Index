import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'
import { chatApi } from '@/api/chat'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

interface Source {
  content: string
  source: string
  score: number
}

interface Conversation {
  id: string
  title: string | null
}

interface ChatState {
  conversations: Conversation[]
  currentId: string | null
  messages: Message[]
  sources: Source[]
  isStreaming: boolean
  _abortController: AbortController | null

  loadConversations: () => Promise<void>
  createConversation: () => Promise<string>
  loadConversation: (id: string) => Promise<void>
  sendMessage: (content: string) => Promise<void>
  stopStreaming: () => void
  deleteConversation: (id: string) => Promise<void>
}

export const useChatStore = create<ChatState>()(
  immer((set, get) => ({
    conversations: [],
    currentId: null,
    messages: [],
    sources: [],
    isStreaming: false,
    _abortController: null,

    loadConversations: async () => {
      const data = await chatApi.listConversations()
      set((s) => {
        s.conversations = data.items
      })
    },

    createConversation: async () => {
      const data = await chatApi.createConversation()
      set((s) => {
        s.conversations.unshift({ id: data.id, title: data.title })
        s.currentId = data.id
        s.messages = []
        s.sources = []
      })
      return data.id
    },

    loadConversation: async (id: string) => {
      const data = await chatApi.getConversation(id)
      set((s) => {
        s.currentId = id
        s.messages = data.messages.map((m) => ({
          id: m.id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
        }))
        s.sources = []
      })
    },

    sendMessage: async (content: string) => {
      const state = get()
      let convId = state.currentId

      if (!convId) {
        convId = await get().createConversation()
      }

      const userMsgId = crypto.randomUUID()
      const assistantMsgId = crypto.randomUUID()

      set((s) => {
        s.messages.push({ id: userMsgId, role: 'user', content })
        s.messages.push({ id: assistantMsgId, role: 'assistant', content: '' })
        s.isStreaming = true
        s.sources = []
      })

      const controller = new AbortController()
      set((s) => {
        s._abortController = controller
      })

      await chatApi.streamChat(
        convId!,
        content,
        {
          onText: (text) => {
            set((s) => {
              const lastMsg = s.messages[s.messages.length - 1]
              if (lastMsg?.role === 'assistant') {
                lastMsg.content += text
              }
            })
          },
          onSource: (sources) => {
            set((s) => {
              s.sources = sources
            })
          },
          onError: (error) => {
            console.error('SSE error:', error)
            set((s) => {
              s.isStreaming = false
            })
          },
          onDone: () => {
            set((s) => {
              s.isStreaming = false
              s._abortController = null
            })
            // Refresh conversation list to get auto-generated title
            get().loadConversations()
          },
        },
        controller.signal,
      )
    },

    stopStreaming: () => {
      const { _abortController } = get()
      _abortController?.abort()
      set((s) => {
        s.isStreaming = false
        s._abortController = null
      })
    },

    deleteConversation: async (id: string) => {
      await chatApi.deleteConversation(id)
      set((s) => {
        s.conversations = s.conversations.filter((c) => c.id !== id)
        if (s.currentId === id) {
          s.currentId = null
          s.messages = []
        }
      })
    },
  })),
)

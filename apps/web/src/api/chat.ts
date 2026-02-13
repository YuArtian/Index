import { request } from '@/service/request'
import { consumeSSE, type SSECallbacks } from '@/service/sse'

interface Conversation {
  id: string
  title: string | null
  created_at: string | null
  updated_at: string | null
}

interface ConversationDetail {
  id: string
  title: string | null
  messages: Array<{
    id: string
    role: string
    content: string
    created_at: string | null
  }>
}

export const chatApi = {
  listConversations: (signal?: AbortSignal) =>
    request.get<unknown, { items: Conversation[]; total: number }>('/conversations', { signal }),

  createConversation: () =>
    request.post<unknown, { id: string; title: string | null }>('/conversations'),

  getConversation: (id: string, signal?: AbortSignal) =>
    request.get<unknown, ConversationDetail>(`/conversations/${id}`, { signal }),

  deleteConversation: (id: string) =>
    request.delete(`/conversations/${id}`),

  streamChat: (
    conversationId: string,
    message: string,
    callbacks: SSECallbacks,
    signal?: AbortSignal,
  ) =>
    consumeSSE(
      'http://localhost:8000/chat',
      { conversation_id: conversationId, message },
      callbacks,
      signal,
    ),
}

import { request } from '@/service/request'

interface Document {
  id: string
  filename: string
  source: string
  status: string
  chunk_count: number
  created_at: string
}

export const knowledgeApi = {
  listDocuments: (signal?: AbortSignal) =>
    request.get<unknown, { documents: Document[]; total: number }>('/documents', { signal }),

  indexDocument: (content: string, source: string, fileType = 'text') =>
    request.post('/index', { content, source, file_type: fileType }),

  deleteDocument: (docId: string) =>
    request.delete(`/documents/${docId}`),

  search: (query: string, topK = 5) =>
    request.post('/search', { query, top_k: topK }),
}

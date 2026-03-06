import { request, BASE_URL } from '@/service/request'

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

  uploadFile: (file: File, highQuality = false) => {
    const form = new FormData()
    form.append('file', file)
    form.append('high_quality', String(highQuality))
    return request.post('/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  deleteDocument: (docId: string) =>
    request.delete(`/documents/${docId}`),

  getDocumentFileUrl: (docId: string) => `${BASE_URL}/documents/${docId}/file`,

  search: (query: string, topK = 5) =>
    request.post('/search', { query, top_k: topK }),
}

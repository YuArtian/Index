import { request } from '@/service/request'

export interface LearningItem {
  id: string
  title: string
  author: string | null
  type: string
  progress: number
  status: string
  document_id: string | null
  filename: string | null
  updated_at: string | null
}

export const progressApi = {
  listItems: (signal?: AbortSignal) =>
    request.get<unknown, { items: LearningItem[]; total: number }>('/progress', { signal }),

  getItem: (id: string, signal?: AbortSignal) =>
    request.get<unknown, LearningItem>(`/progress/${id}`, { signal }),

  createItem: (data: { title: string; author?: string; document_id?: string }) =>
    request.post('/progress', data),

  updateItem: (id: string, data: { title?: string; author?: string; progress?: number; status?: string; notes?: string }) =>
    request.put(`/progress/${id}`, data),

  deleteItem: (id: string) =>
    request.delete(`/progress/${id}`),
}

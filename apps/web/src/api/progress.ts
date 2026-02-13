import { request } from '@/service/request'

interface LearningItem {
  id: string
  title: string
  author: string | null
  type: string
  total_chapters: number
  completed_chapters: number
  status: string
  updated_at: string | null
}

interface LearningItemDetail extends LearningItem {
  notes: string | null
  chapters: Array<{
    id: string
    title: string
    chapter_index: number
    status: string
    completed_at: string | null
    notes: string | null
  }>
}

export const progressApi = {
  listItems: (signal?: AbortSignal) =>
    request.get<unknown, { items: LearningItem[]; total: number }>('/progress', { signal }),

  getItem: (id: string, signal?: AbortSignal) =>
    request.get<unknown, LearningItemDetail>(`/progress/${id}`, { signal }),

  createItem: (data: { title: string; author?: string; chapters?: string[] }) =>
    request.post('/progress', data),

  updateItem: (id: string, data: { title?: string; author?: string; status?: string; notes?: string }) =>
    request.put(`/progress/${id}`, data),

  deleteItem: (id: string) =>
    request.delete(`/progress/${id}`),

  updateChapter: (itemId: string, chapterId: string, data: { status?: string; notes?: string }) =>
    request.put(`/progress/${itemId}/chapters/${chapterId}`, data),
}

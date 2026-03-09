import { request } from '@/service/request'

export interface GraphNode {
  name: string
  category: string
  description: string
  connections: number
}

export interface GraphEdge {
  source: string
  target: string
  relation: string
  weight: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface GraphStats {
  concepts: number
  relations: number
}

export const graphApi = {
  getGraph: (limit = 200) =>
    request.get<unknown, GraphData>('/graph', { params: { limit } }),

  getStats: () =>
    request.get<unknown, GraphStats>('/graph/stats'),

  searchConcepts: (q: string, limit = 20) =>
    request.get<unknown, GraphNode[]>('/graph/search', { params: { q, limit } }),

  getNeighbors: (conceptName: string, depth = 2) =>
    request.get<unknown, GraphData>(`/graph/neighbors/${encodeURIComponent(conceptName)}`, {
      params: { depth },
    }),
}

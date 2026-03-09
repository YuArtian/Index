import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'
import { graphApi, type GraphNode, type GraphEdge, type GraphStats } from '@/api/graph'

interface GraphState {
  nodes: GraphNode[]
  edges: GraphEdge[]
  stats: GraphStats
  selectedNode: GraphNode | null
  loading: boolean
  categoryFilter: string | null

  loadGraph: () => Promise<void>
  loadStats: () => Promise<void>
  selectNode: (node: GraphNode | null) => void
  focusNode: (name: string) => Promise<void>
  setCategoryFilter: (category: string | null) => void
}

export const useGraphStore = create<GraphState>()(
  immer((set) => ({
    nodes: [],
    edges: [],
    stats: { concepts: 0, relations: 0 },
    selectedNode: null,
    loading: false,
    categoryFilter: null,

    loadGraph: async () => {
      set((s) => { s.loading = true })
      try {
        const data = await graphApi.getGraph()
        set((s) => {
          s.nodes = data.nodes
          s.edges = data.edges
          s.loading = false
        })
      } catch {
        set((s) => { s.loading = false })
      }
    },

    loadStats: async () => {
      try {
        const data = await graphApi.getStats()
        set((s) => { s.stats = data })
      } catch {
        // ignore
      }
    },

    selectNode: (node) => {
      set((s) => { s.selectedNode = node })
    },

    focusNode: async (name: string) => {
      try {
        const data = await graphApi.getNeighbors(name)
        set((s) => {
          s.nodes = data.nodes
          s.edges = data.edges
          s.selectedNode = data.nodes.find((n) => n.name === name) ?? null
        })
      } catch {
        // ignore
      }
    },

    setCategoryFilter: (category) => {
      set((s) => { s.categoryFilter = category })
    },
  })),
)

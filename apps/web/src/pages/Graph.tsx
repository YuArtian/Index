import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import { Search, RotateCcw, X } from 'lucide-react'
import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d'
import { useGraphStore } from '@/stores/graph'
import { graphApi, type GraphNode } from '@/api/graph'

// Category → color mapping
const CATEGORY_COLORS: Record<string, string> = {
  '技术': '#3b82f6',
  '概念': '#8b5cf6',
  '工具': '#f59e0b',
  '语言': '#a855f7',
  '框架': '#10b981',
  '算法': '#f97316',
  '设计模式': '#06b6d4',
  '原理': '#ec4899',
  '人物': '#6366f1',
  '其他': '#6b7280',
}

const ALL_CATEGORIES = Object.keys(CATEGORY_COLORS)

function getNodeColor(category: string) {
  return CATEGORY_COLORS[category] ?? CATEGORY_COLORS['其他']
}

function getNodeSize(connections: number) {
  return Math.max(4, Math.min(16, 4 + connections * 1.5))
}

// Build graph data for react-force-graph
interface FGNode {
  id: string
  name: string
  category: string
  description: string
  connections: number
  color: string
  val: number
}

interface FGLink {
  source: string
  target: string
  relation: string
  weight: number
}

export default function GraphPage() {
  const {
    nodes, edges, stats, selectedNode, loading, categoryFilter,
    loadGraph, loadStats, selectNode, focusNode, setCategoryFilter,
  } = useGraphStore()

  const graphRef = useRef<ForceGraphMethods<FGNode, FGLink>>(undefined)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<GraphNode[]>([])
  const [highlightedNode, setHighlightedNode] = useState<string | null>(null)
  const searchTimerRef = useRef<ReturnType<typeof setTimeout>>(null)

  // Load graph data on mount
  useEffect(() => {
    loadGraph()
    loadStats()
  }, [loadGraph, loadStats])

  // Resize observer for the graph container
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect
      setDimensions({ width, height })
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  // Debounced search
  useEffect(() => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
    if (!searchQuery.trim()) {
      setSearchResults([])
      setHighlightedNode(null)
      return
    }
    searchTimerRef.current = setTimeout(async () => {
      try {
        const results = await graphApi.searchConcepts(searchQuery, 10)
        setSearchResults(results)
        if (results.length > 0) {
          setHighlightedNode(results[0].name)
        }
      } catch {
        setSearchResults([])
      }
    }, 300)
  }, [searchQuery])

  // Build filtered graph data
  const graphData = useMemo(() => {
    const filteredNodes = categoryFilter
      ? nodes.filter((n) => n.category === categoryFilter)
      : nodes
    const nodeSet = new Set(filteredNodes.map((n) => n.name))

    const fgNodes: FGNode[] = filteredNodes.map((n) => ({
      id: n.name,
      name: n.name,
      category: n.category,
      description: n.description,
      connections: n.connections,
      color: getNodeColor(n.category),
      val: getNodeSize(n.connections),
    }))

    const fgLinks: FGLink[] = edges
      .filter((e) => nodeSet.has(e.source) && nodeSet.has(e.target))
      .map((e) => ({
        source: e.source,
        target: e.target,
        relation: e.relation,
        weight: e.weight,
      }))

    return { nodes: fgNodes, links: fgLinks }
  }, [nodes, edges, categoryFilter])

  // Categories present in current data
  const activeCategories = useMemo(() => {
    const cats = new Set(nodes.map((n) => n.category))
    return ALL_CATEGORIES.filter((c) => cats.has(c))
  }, [nodes])

  const handleNodeClick = useCallback((node: FGNode) => {
    selectNode({
      name: node.name,
      category: node.category,
      description: node.description,
      connections: node.connections,
    })
    setHighlightedNode(node.id)
  }, [selectNode])

  const handleNodeDblClick = useCallback((node: FGNode) => {
    focusNode(node.name)
  }, [focusNode])

  const handleSearchResultClick = (result: GraphNode) => {
    setHighlightedNode(result.name)
    setSearchQuery('')
    setSearchResults([])
    selectNode(result)
    // Fly to node
    const fgNode = graphData.nodes.find((n) => n.id === result.name)
    if (fgNode && graphRef.current) {
      graphRef.current.centerAt(
        (fgNode as FGNode & { x?: number }).x,
        (fgNode as FGNode & { y?: number }).y,
        800,
      )
      graphRef.current.zoom(3, 800)
    }
  }

  const handleReset = () => {
    setCategoryFilter(null)
    setHighlightedNode(null)
    setSearchQuery('')
    setSearchResults([])
    selectNode(null)
    loadGraph()
    loadStats()
  }

  // Custom node canvas rendering
  const paintNode = useCallback((node: FGNode, ctx: CanvasRenderingContext2D) => {
    const size = node.val
    const isHighlighted = highlightedNode === node.id

    // Glow effect for highlighted node
    if (isHighlighted) {
      ctx.beginPath()
      ctx.arc(node.x!, node.y!, size + 4, 0, 2 * Math.PI)
      ctx.fillStyle = node.color + '40'
      ctx.fill()
    }

    // Node circle
    ctx.beginPath()
    ctx.arc(node.x!, node.y!, size, 0, 2 * Math.PI)
    ctx.fillStyle = isHighlighted ? node.color : node.color + 'cc'
    ctx.fill()
    ctx.strokeStyle = isHighlighted ? '#fff' : node.color
    ctx.lineWidth = isHighlighted ? 2 : 0.5
    ctx.stroke()

    // Label (only for larger nodes or highlighted)
    if (size >= 6 || isHighlighted) {
      ctx.font = `${isHighlighted ? 'bold ' : ''}${Math.max(3, size * 0.8)}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillStyle = '#374151'
      ctx.fillText(node.name, node.x!, node.y! + size + 2)
    }
  }, [highlightedNode])

  // Empty state
  if (!loading && nodes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-400">
          <div className="text-5xl mb-4">🕸️</div>
          <p className="text-lg font-medium mb-2">知识图谱为空</p>
          <p className="text-sm">去知识库上传文档，系统会自动提取概念构建图谱</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 bg-white shrink-0">
        {/* Search */}
        <div className="relative w-64">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索概念..."
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {/* Search dropdown */}
          {searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 max-h-60 overflow-y-auto">
              {searchResults.map((r) => (
                <button
                  key={r.name}
                  onClick={() => handleSearchResultClick(r)}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2"
                >
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: getNodeColor(r.category) }}
                  />
                  <span className="truncate">{r.name}</span>
                  <span className="text-xs text-gray-400 ml-auto shrink-0">{r.category}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Category filters */}
        <div className="flex items-center gap-1 flex-1 overflow-x-auto">
          {activeCategories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(categoryFilter === cat ? null : cat)}
              className={`px-2.5 py-1 text-xs rounded-full whitespace-nowrap transition-colors ${
                categoryFilter === cat
                  ? 'text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              style={categoryFilter === cat ? { backgroundColor: getNodeColor(cat) } : undefined}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Reset button */}
        <button
          onClick={handleReset}
          className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors"
          title="重置视图"
        >
          <RotateCcw size={16} />
        </button>
      </div>

      {/* Main area */}
      <div className="flex flex-1 min-h-0">
        {/* Graph canvas */}
        <div ref={containerRef} className="flex-1 relative bg-gray-50">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/60 z-10">
              <p className="text-sm text-gray-500">加载中...</p>
            </div>
          )}
          <ForceGraph2D
            ref={graphRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            nodeId="id"
            nodeCanvasObject={paintNode}
            nodePointerAreaPaint={(node: FGNode, color, ctx) => {
              ctx.beginPath()
              ctx.arc(node.x!, node.y!, node.val + 2, 0, 2 * Math.PI)
              ctx.fillStyle = color
              ctx.fill()
            }}
            linkColor={() => '#d1d5db'}
            linkWidth={(link: FGLink) => Math.max(0.5, link.weight * 0.5)}
            linkDirectionalArrowLength={3}
            linkDirectionalArrowRelPos={1}
            onNodeClick={handleNodeClick}
            onNodeDblClick={handleNodeDblClick}
            cooldownTicks={100}
            enableZoomInteraction={true}
            enablePanInteraction={true}
          />
        </div>

        {/* Detail panel */}
        {selectedNode && (
          <div className="w-72 border-l border-gray-200 bg-white p-4 overflow-y-auto shrink-0">
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-base font-bold text-gray-900">{selectedNode.name}</h3>
              <button
                onClick={() => { selectNode(null); setHighlightedNode(null) }}
                className="p-0.5 text-gray-400 hover:text-gray-600"
              >
                <X size={16} />
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <span className="text-gray-500">类别</span>
                <span
                  className="ml-2 px-2 py-0.5 rounded-full text-xs text-white"
                  style={{ backgroundColor: getNodeColor(selectedNode.category) }}
                >
                  {selectedNode.category}
                </span>
              </div>

              {selectedNode.description && (
                <div>
                  <p className="text-gray-500 mb-1">描述</p>
                  <p className="text-gray-700">{selectedNode.description}</p>
                </div>
              )}

              <div>
                <span className="text-gray-500">连接数</span>
                <span className="ml-2 text-gray-900 font-medium">{selectedNode.connections}</span>
              </div>

              {/* Related nodes from edges */}
              <div>
                <p className="text-gray-500 mb-2">关联概念</p>
                <div className="space-y-1.5">
                  {edges
                    .filter((e) => e.source === selectedNode.name || e.target === selectedNode.name)
                    .map((e, i) => {
                      const other = e.source === selectedNode.name ? e.target : e.source
                      const direction = e.source === selectedNode.name ? '→' : '←'
                      return (
                        <button
                          key={i}
                          onClick={() => {
                            const node = nodes.find((n) => n.name === other)
                            if (node) {
                              selectNode(node)
                              setHighlightedNode(other)
                            }
                          }}
                          className="w-full text-left px-2 py-1.5 rounded-md hover:bg-gray-50 flex items-center gap-1.5 text-xs transition-colors"
                        >
                          <span className="text-gray-400">{direction}</span>
                          <span className="text-blue-600 truncate">{other}</span>
                          <span className="text-gray-400 ml-auto shrink-0">{e.relation}</span>
                        </button>
                      )
                    })}
                </div>
              </div>

              <button
                onClick={() => focusNode(selectedNode.name)}
                className="w-full mt-2 px-3 py-1.5 text-xs bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
              >
                展开此节点的关联图
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Bottom stats bar */}
      <div className="flex items-center gap-6 px-4 py-2 border-t border-gray-200 bg-white text-xs text-gray-500 shrink-0">
        <span>概念 <strong className="text-gray-700">{stats.concepts}</strong></span>
        <span>关系 <strong className="text-gray-700">{stats.relations}</strong></span>
        {categoryFilter && (
          <span className="ml-auto">
            筛选: {categoryFilter}
            <button onClick={() => setCategoryFilter(null)} className="ml-1 text-gray-400 hover:text-gray-600">✕</button>
          </span>
        )}
      </div>
    </div>
  )
}

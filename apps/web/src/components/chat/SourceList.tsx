interface Source {
  content: string
  source: string
  score: number
}

interface Props {
  sources: Source[]
}

export function SourceList({ sources }: Props) {
  if (sources.length === 0) return null

  return (
    <div className="border-t border-gray-200 p-4 bg-gray-50">
      <p className="text-xs text-gray-500 mb-2 font-medium">参考来源</p>
      <div className="space-y-2">
        {sources.map((s, i) => (
          <div key={i} className="text-xs bg-white rounded-lg p-2 border border-gray-200">
            <div className="flex justify-between items-center mb-1">
              <span className="text-gray-600 font-medium">{s.source}</span>
              <span className="text-gray-400">{(s.score * 100).toFixed(0)}%</span>
            </div>
            <p className="text-gray-500 line-clamp-2">{s.content}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

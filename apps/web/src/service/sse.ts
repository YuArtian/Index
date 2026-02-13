export interface SSECallbacks {
  onText: (text: string) => void
  onSource?: (sources: Array<{ content: string; source: string; score: number }>) => void
  onError?: (error: string) => void
  onDone?: () => void
}

export async function consumeSSE(
  url: string,
  body: object,
  callbacks: SSECallbacks,
  signal?: AbortSignal,
) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })

  if (!res.ok || !res.body) {
    callbacks.onError?.(`HTTP ${res.status}`)
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        switch (data.type) {
          case 'text':
            callbacks.onText(data.text)
            break
          case 'source':
            callbacks.onSource?.(data.sources)
            break
          case 'error':
            callbacks.onError?.(data.message)
            break
          case 'done':
            callbacks.onDone?.()
            break
        }
      } catch {
        // skip malformed lines
      }
    }
  }
}

import { useEffect, useRef, useCallback } from 'react'
import * as pdfjsLib from 'pdfjs-dist'
import {
  PDFViewer,
  EventBus,
  PDFLinkService,
} from 'pdfjs-dist/web/pdf_viewer.mjs'
import 'pdfjs-dist/web/pdf_viewer.css'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

interface Props {
  url: string
  initialProgress?: number // 0-100, will be converted to page number
  onPageChange?: (page: number, totalPages: number) => void
  onTextSelect?: (text: string) => void
}

export default function PdfViewerComponent({
  url,
  initialProgress = 0,
  onPageChange,
  onTextSelect,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewerRef = useRef<PDFViewer | null>(null)
  const eventBusRef = useRef<EventBus | null>(null)

  // Text selection handler
  const handleMouseUp = useCallback(() => {
    const selection = window.getSelection()
    const text = selection?.toString().trim()
    if (text && onTextSelect) {
      onTextSelect(text)
    }
  }, [onTextSelect])

  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    const eventBus = new EventBus()
    eventBusRef.current = eventBus

    const linkService = new PDFLinkService({ eventBus })
    const viewer = new PDFViewer({
      container,
      eventBus,
      linkService,
      textLayerMode: 2,
      removePageBorders: true,
    })
    viewerRef.current = viewer
    linkService.setViewer(viewer)

    // Track page changes
    eventBus.on('pagechanging', (evt: { pageNumber: number }) => {
      if (onPageChange && viewer.pagesCount) {
        onPageChange(evt.pageNumber, viewer.pagesCount)
      }
    })

    // Load document
    const loadTask = pdfjsLib.getDocument(url)
    loadTask.promise.then((doc) => {
      viewer.setDocument(doc)
      linkService.setDocument(doc)

      // Jump to saved progress after pages are ready
      if (initialProgress > 0) {
        eventBus.on('pagesloaded', () => {
          const targetPage = Math.max(1, Math.round((initialProgress / 100) * doc.numPages))
          viewer.currentPageNumber = targetPage
        })
      }
    })

    // Fit to container width
    const resizeObserver = new ResizeObserver(() => {
      if (viewer.pagesCount) {
        viewer.currentScaleValue = 'page-width'
      }
    })
    resizeObserver.observe(container)

    // Text selection listener
    container.addEventListener('mouseup', handleMouseUp)

    return () => {
      container.removeEventListener('mouseup', handleMouseUp)
      resizeObserver.disconnect()
      viewer.cleanup()
      loadTask.destroy()
    }
  }, [url]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-auto absolute inset-0"
      style={{ background: '#f3f4f6' }}
    >
      <div className="pdfViewer" />
    </div>
  )
}

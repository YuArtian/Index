import { useEffect, useRef, useCallback, useImperativeHandle, forwardRef } from 'react'
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

export interface OutlineItem {
  title: string
  dest: unknown
  items: OutlineItem[]
}

export interface PdfViewerHandle {
  goToDestination: (dest: unknown) => void
  goToPage: (page: number) => void
}

interface Props {
  url: string
  initialProgress?: number
  onPageChange?: (page: number, totalPages: number) => void
  onTextSelect?: (text: string) => void
  onOutlineLoaded?: (outline: OutlineItem[]) => void
}

const PdfViewerComponent = forwardRef<PdfViewerHandle, Props>(function PdfViewerComponent(
  { url, initialProgress = 0, onPageChange, onTextSelect, onOutlineLoaded },
  ref,
) {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewerRef = useRef<PDFViewer | null>(null)
  const linkServiceRef = useRef<PDFLinkService | null>(null)

  useImperativeHandle(ref, () => ({
    goToDestination(dest: unknown) {
      linkServiceRef.current?.goToDestination(dest as string | unknown[])
    },
    goToPage(page: number) {
      if (viewerRef.current) {
        viewerRef.current.currentPageNumber = page
      }
    },
  }))

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

    const linkService = new PDFLinkService({ eventBus })
    linkServiceRef.current = linkService
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

      // Extract outline
      doc.getOutline().then((outline) => {
        if (outline && onOutlineLoaded) {
          onOutlineLoaded(outline as OutlineItem[])
        }
      })

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
})

export default PdfViewerComponent

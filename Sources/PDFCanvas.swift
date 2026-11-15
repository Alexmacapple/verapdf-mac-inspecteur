import AppKit
import PDFKit
import SwiftUI

/// Les actions embarquées et les menus de lien du PDF restent inactifs.
final class ReadOnlyPDFView: PDFView {
    var requestedZoom: CGFloat = 1
    private var previousSize: NSSize = .zero
    override func perform(_ action: PDFAction) {}
    override func menu(for event: NSEvent) -> NSMenu? { nil }
    override func layout() {
        super.layout()
        if previousSize != bounds.size {
            previousSize = bounds.size
            DispatchQueue.main.async { [weak self] in self?.fitPage() }
        }
    }
    func fitPage() {
        guard bounds.width > 100, bounds.height > 100, document != nil else { return }
        autoScales = true
        layoutDocumentView()
        scaleFactor = scaleFactorForSizeToFit * requestedZoom
    }
}

final class HighlightLayer: NSView {
    weak var pdf: PDFView?
    var pageNumber = 1
    var rectangles: [[Double]] = []
    override func hitTest(_ point: NSPoint) -> NSView? { nil }
    var visibleRectangles: [[Double]] {
        guard let pdf, let page = pdf.document?.page(at: pageNumber - 1), pdf.currentPage === page else { return [] }
        return rectangles
    }
    override func draw(_ dirtyRect: NSRect) {
        guard let pdf, let page = pdf.document?.page(at: pageNumber - 1) else { return }
        for r in visibleRectangles where r.count == 4 {
            let bounds = CGRect(x: r[0], y: r[1], width: r[2]-r[0], height: r[3]-r[1])
            let box = convert(pdf.convert(bounds, from: page), from: pdf)
            NSColor.systemOrange.withAlphaComponent(0.14).setFill()
            NSBezierPath(rect: box).fill()
            NSColor.systemOrange.setStroke()
            let path = NSBezierPath(rect: box)
            path.lineWidth = 3
            path.stroke()
        }
    }
}

struct PDFCanvas: NSViewRepresentable {
    let url: URL?
    let generation: UUID
    @Binding var page: Int
    let zoom: CGFloat
    let fitRequest: UUID
    let rectangles: [[Double]]
    final class Coordinator {
        var generation: UUID?
        var zoom: CGFloat = 0
        var fitRequest: UUID?
        var observers: [NSObjectProtocol] = []
        var page: Binding<Int>?
        var updating = false
        func synchronizePage(_ view: PDFView) {
            guard !updating, let document = view.document, let current = view.currentPage else { return }
            let index = document.index(for: current)
            guard index != NSNotFound else { return }
            page?.wrappedValue = index + 1
        }
        deinit { observers.forEach(NotificationCenter.default.removeObserver) }
    }
    func makeCoordinator() -> Coordinator { Coordinator() }
    func makeNSView(context: Context) -> ReadOnlyPDFView {
        let view = ReadOnlyPDFView()
        view.autoScales = true
        view.displayMode = .singlePage
        view.backgroundColor = .underPageBackgroundColor
        view.setAccessibilityLabel("Aperçu du PDF en lecture seule")
        let layer = HighlightLayer(frame: view.bounds)
        layer.pdf = view
        layer.autoresizingMask = [.width, .height]
        layer.setAccessibilityElement(false)
        view.addSubview(layer)
        for name in [Notification.Name.PDFViewScaleChanged, .PDFViewPageChanged] {
            let coordinator = context.coordinator
            coordinator.observers.append(NotificationCenter.default.addObserver(forName: name, object: view, queue: .main) { [weak view, weak coordinator] notification in
                layer.needsDisplay = true
                if notification.name == .PDFViewPageChanged, let view { coordinator?.synchronizePage(view) }
            })
        }
        return view
    }
    func updateNSView(_ view: ReadOnlyPDFView, context: Context) {
        context.coordinator.page = $page
        context.coordinator.updating = true
        defer { context.coordinator.updating = false }
        if context.coordinator.generation != generation {
            view.document = url.flatMap(PDFDocument.init(url:))
            context.coordinator.generation = generation
            context.coordinator.zoom = 0
        }
        if let target = view.document?.page(at: page-1), view.currentPage !== target { view.go(to: target) }
        if context.coordinator.zoom != zoom || context.coordinator.fitRequest != fitRequest {
            view.requestedZoom = zoom
            DispatchQueue.main.async { view.fitPage() }
            context.coordinator.zoom = zoom
            context.coordinator.fitRequest = fitRequest
        }
        if let layer = view.subviews.compactMap({ $0 as? HighlightLayer }).first {
            layer.pageNumber = page
            layer.rectangles = rectangles
            layer.needsDisplay = true
        }
    }
}

import AppKit
import PDFKit
import SwiftUI

// Vérifie les vraies classes PDFKit après une navigation interne au visualiseur.
let app = NSApplication.shared
app.setActivationPolicy(.prohibited)
let document = PDFDocument()
let bitmap = CGContext(data: nil, width: 300, height: 400, bitsPerComponent: 8,
                       bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(),
                       bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
let image = NSImage(cgImage: bitmap.makeImage()!, size: NSSize(width: 300, height: 400))
document.insert(PDFPage(image: image)!, at: 0)
document.insert(PDFPage(image: image)!, at: 1)
let view = ReadOnlyPDFView(frame: NSRect(x: 0, y: 0, width: 600, height: 700))
view.displayMode = .singlePage
view.document = document
let layer = HighlightLayer()
layer.pdf = view
layer.pageNumber = 1
layer.rectangles = [[10, 20, 40, 50]]
view.go(to: document.page(at: 0)!)
precondition(layer.visibleRectangles.count == 1, "La zone de la page courante doit être visible.")
var modelPage = 1
let coordinator = PDFCanvas.Coordinator()
coordinator.page = Binding(get: { modelPage }, set: { modelPage = $0 })
let observer = NotificationCenter.default.addObserver(forName: .PDFViewPageChanged, object: view, queue: .main) { _ in
    coordinator.synchronizePage(view)
}
view.goToNextPage(nil)
precondition(view.currentPage === document.page(at: 1), "La navigation doit atteindre la deuxième page.")
precondition(modelPage == 2, "La notification doit synchroniser la page du modèle.")
precondition(layer.visibleRectangles.isEmpty, "Les zones de la page précédente doivent disparaître immédiatement.")
layer.pageNumber = 2
precondition(layer.visibleRectangles.count == 1, "Les zones de la nouvelle page peuvent être affichées.")
coordinator.updating = true
view.go(to: document.page(at: 0)!)
precondition(modelPage == 2, "Une mise à jour programmée ne doit pas republier l’état SwiftUI.")
NotificationCenter.default.removeObserver(observer)
print("PDFKit : navigation, synchronisation et suppression des anciens surlignages vérifiées.")

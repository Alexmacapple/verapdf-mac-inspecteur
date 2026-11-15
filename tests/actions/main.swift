import AppKit
import SwiftUI
import PDFKit
import ObjectiveC

@MainActor private var panelCalls = 0
extension NSOpenPanel {
    @objc func inspector_test_runModal() -> NSApplication.ModalResponse {
        panelCalls += 1
        return .cancel
    }
}

@main
struct ActionTests {
    @MainActor static func pump() {
        RunLoop.current.run(until: Date().addingTimeInterval(0.4))
    }
    @MainActor static func pdfView(_ root: NSView) -> ReadOnlyPDFView? {
        if let pdf = root as? ReadOnlyPDFView { return pdf }
        return root.subviews.compactMap { pdfView($0) }.first
    }
    @MainActor static func main() throws {
        let app = NSApplication.shared
        app.setActivationPolicy(.prohibited)
        let model = Inspector()
        var failures: [String] = []
        // Le dialogue est intercepté dans ce processus de test uniquement.
        let original = class_getInstanceMethod(NSOpenPanel.self, #selector(NSOpenPanel.runModal))!
        let replacement = class_getInstanceMethod(NSOpenPanel.self, #selector(NSOpenPanel.inspector_test_runModal))!
        method_exchangeImplementations(original, replacement)
        defer { method_exchangeImplementations(original, replacement) }
        model.busy = true
        model.choosePDF()
        if panelCalls != 0 { failures.append("Un traitement en cours ne doit pas ouvrir un deuxième sélecteur de PDF.") }
        model.busy = false
        let host = NSHostingView(rootView: InspectorView(model: model))
        let window = NSWindow(contentRect: NSRect(x: -6000, y: -6000, width: 1400, height: 900),
                              styleMask: [.titled], backing: .buffered, defer: false)
        window.contentView = host
        window.orderFront(nil)
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: folder) }
        let path = folder.appendingPathComponent("zoom.pdf")
        let document = PDFDocument()
        document.insert(PDFPage(), at: 0)
        precondition(document.write(to: path))
        model.pdfURL = path
        model.pageCount = 1
        pump()
        window.layoutIfNeeded()
        guard let pdf = pdfView(host) else { throw NSError(domain: "Actions", code: 2) }
        pdf.fitPage()
        pump()
        let fitted = pdf.scaleFactor
        pdf.scaleFactor = fitted * 2
        pump()
        #if SHIPGUARD_BASELINE
        // Expression exacte de l’ancien bouton Ajuster, pour constater l’échec avant correction.
        model.zoom = 1
        #else
        model.adjustZoom()
        #endif
        pump()
        if abs(pdf.scaleFactor-fitted) > 0.01 {
            failures.append("Ajuster doit rétablir l’échelle après un zoom natif, même si le modèle vaut déjà 1.")
        }
        if !failures.isEmpty {
            throw NSError(domain: "Actions", code: 3, userInfo: [NSLocalizedDescriptionKey: failures.joined(separator: "\n")])
        }
        print("Actions SwiftUI/PDFKit : deuxième ouverture bloquée et Ajuster après zoom natif vérifiés.")
    }
}

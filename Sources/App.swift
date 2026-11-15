import AppKit
import SwiftUI
import UniformTypeIdentifiers

extension Inspector {
    func choosePDF() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.pdf]
        panel.canChooseDirectories = false
        panel.message = "Choisir le PDF à examiner. L’original restera intact."
        if panel.runModal() == .OK, let url = panel.url { run(pdf: url) }
    }
    func chooseReport() {
        guard let pdfURL else { return }
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.xml]
        panel.message = "Choisir le rapport XML veraPDF PDF/UA-1 de ce document."
        if panel.runModal() == .OK, let url = panel.url { run(pdf: pdfURL, report: url) }
    }
    func saveReport() {
        guard let inspection else { return }
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.xml]
        panel.nameFieldStringValue = "rapport-verapdf.xml"
        if panel.runModal() == .OK, let target = panel.url {
            do { try Data(contentsOf: URL(fileURLWithPath: inspection.reportPath)).write(to: target, options: .atomic) }
            catch { self.error = "Enregistrement impossible : \(error.localizedDescription)" }
        }
    }
    #if INSPECTOR_DIAGNOSTICS
    func captureIfRequested() {
        let args = CommandLine.arguments
        guard let index = args.firstIndex(of: "--capture"), args.indices.contains(index+1) else { return }
        DispatchQueue.main.asyncAfter(deadline: .now()+2) {
            guard let window = NSApp.windows.first(where: { $0.isVisible }), let view = window.contentView,
                  let rep = view.bitmapImageRepForCachingDisplay(in: view.bounds) else { return }
            let metadata: [String: Any] = ["pid": ProcessInfo.processInfo.processIdentifier,
                "window": window.windowNumber, "page": self.page,
                "selected": self.selectedID ?? "", "issues": self.inspection?.issues.count ?? 0,
                "zones": self.currentLocation?.rects.count ?? 0]
            if let data = try? JSONSerialization.data(withJSONObject: metadata, options: .prettyPrinted) {
                try? data.write(to: URL(fileURLWithPath: args[index+1]+".json"))
            }
            view.cacheDisplay(in: view.bounds, to: rep)
            if let png = rep.representation(using: .png, properties: [:]) {
                try? png.write(to: URL(fileURLWithPath: args[index+1]))
            }
        }
    }
    #endif
}

@main
struct InspectorApp: App {
    @StateObject private var model = Inspector()
    var body: some Scene {
        WindowGroup {
            InspectorView(model: model).onAppear {
                NSApp.setActivationPolicy(.regular)
                NSApp.activate(ignoringOtherApps: true)
                let args = CommandLine.arguments
                if model.pdfURL == nil, let i = args.firstIndex(of: "--pdf"), args.indices.contains(i+1) {
                    let pdf = URL(fileURLWithPath: args[i+1])
                    let r = args.firstIndex(of: "--report")
                    let report = r.flatMap { args.indices.contains($0+1) ? URL(fileURLWithPath: args[$0+1]) : nil }
                    model.run(pdf: pdf, report: report)
                }
            }
        }.defaultSize(width: 1400, height: 900)
        .commands {
            CommandGroup(replacing: .newItem) {
                Button("Ouvrir un PDF…", action: model.choosePDF).keyboardShortcut("o").disabled(model.busy)
            }
            CommandGroup(replacing: .saveItem) {
                Button("Enregistrer le rapport XML…", action: model.saveReport).keyboardShortcut("s").disabled(model.inspection == nil)
            }
        }
    }
}

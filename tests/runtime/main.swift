import Foundation
import PDFKit
import Darwin

@main
struct RuntimeTests {
    @MainActor static func wait(_ condition: () -> Bool) {
        let end = Date().addingTimeInterval(8)
        while !condition() && Date() < end { RunLoop.current.run(until: Date().addingTimeInterval(0.02)) }
        precondition(condition(), "Le traitement doit se terminer dans le délai du test.")
    }

    @MainActor static func main() throws {
        let root = URL(fileURLWithPath: CommandLine.arguments[1])
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: folder) }
        let model = Inspector()
        model.pythonExecutable = CommandLine.arguments[2]
        model.workerScript = root.appendingPathComponent("tests/runtime/worker_fixture.py")
        model.reportFolder = folder
        let good = folder.appendingPathComponent("good.pdf")
        model.run(pdf: good)
        wait { !model.busy }
        precondition(model.inspection != nil && model.pdfURL == good && model.pageCount == 2)
        model.page = 2
        model.run(pdf: good, report: folder.appendingPathComponent("refus.xml"))
        wait { !model.busy }
        precondition(model.inspection != nil && model.pdfURL == good && model.page == 2 && model.error != nil,
                     "Un import refusé doit conserver le diagnostic et la page.")
        model.run(pdf: folder.appendingPathComponent("sleep-cancel.pdf"))
        let marker = folder.appendingPathComponent("enfant.pid")
        wait { FileManager.default.fileExists(atPath: marker.path) }
        let child = Int32(try String(contentsOf: marker, encoding: .utf8).trimmingCharacters(in: .whitespacesAndNewlines))!
        model.cancel()
        wait { !model.busy }
        wait { kill(child, 0) != 0 }
        precondition(model.inspection != nil && model.pdfURL == good && model.page == 2,
                     "L’annulation doit préserver le diagnostic et arrêter les descendants.")
        try FileManager.default.removeItem(at: marker)
        model.workerTimeout = 0.4
        model.run(pdf: folder.appendingPathComponent("sleep-timeout.pdf"))
        wait { FileManager.default.fileExists(atPath: marker.path) }
        let timedChild = Int32(try String(contentsOf: marker, encoding: .utf8).trimmingCharacters(in: .whitespacesAndNewlines))!
        wait { !model.busy }
        wait { kill(timedChild, 0) != 0 }
        precondition(model.error?.contains("Délai global") == true && model.inspection != nil,
                     "Le délai global doit arrêter tout le groupe et conserver le résultat.")
        try FileManager.default.removeItem(at: marker)
        model.workerTimeout = 10
        model.run(pdf: folder.appendingPathComponent("sleep-stubborn.pdf"))
        wait { FileManager.default.fileExists(atPath: marker.path) }
        let stubborn = Int32(try String(contentsOf: marker, encoding: .utf8).trimmingCharacters(in: .whitespacesAndNewlines))!
        // Le temps laissé au sous-processus permet l’installation de son refus SIGTERM.
        RunLoop.current.run(until: Date().addingTimeInterval(0.2))
        model.cancel()
        wait { !model.busy }
        wait { kill(stubborn, 0) != 0 }
        precondition(model.inspection != nil, "Le secours SIGKILL doit arrêter un descendant récalcitrant.")

        let fresh = Inspector()
        fresh.pythonExecutable = model.pythonExecutable
        fresh.workerScript = model.workerScript
        fresh.reportFolder = folder
        let bad = folder.appendingPathComponent("bad-initial.pdf")
        let doc = PDFDocument()
        doc.insert(PDFPage(), at: 0)
        doc.insert(PDFPage(), at: 1)
        precondition(doc.write(to: bad))
        fresh.run(pdf: bad)
        wait { !fresh.busy }
        precondition(fresh.inspection == nil && fresh.pageCount == 2 && fresh.pdfURL == bad,
                     "Le PDF doit rester navigable après un premier contrôle refusé.")

        let cache = folder.appendingPathComponent("cache")
        try FileManager.default.createDirectory(at: cache, withIntermediateDirectories: true)
        let active = cache.appendingPathComponent("111111111111-111111111111.xml")
        let old = cache.appendingPathComponent("222222222222-222222222222.xml")
        let recent = cache.appendingPathComponent("333333333333-333333333333.xml")
        let imported = cache.appendingPathComponent("rapport-utilisateur.xml")
        for file in [active, old, recent, imported] { try Data().write(to: file) }
        try FileManager.default.setAttributes([.modificationDate: Date().addingTimeInterval(-40 * 86400)], ofItemAtPath: old.path)
        var recycled: [URL] = []
        let count = try ReportCache.prune(folder: cache, protecting: active, keep: 2) { recycled.append($0) }
        precondition(count == 1 && recycled.map(\.lastPathComponent) == [old.lastPathComponent], "Le cache doit préserver le rapport actif et les imports : \(count), \(recycled).")
        recycled = []
        _ = try ReportCache.prune(folder: cache, protecting: active, keep: 0) { recycled.append($0) }
        precondition(Set(recycled.map(\.lastPathComponent)) == Set([old, recent].map(\.lastPathComponent)), "La purge manuelle exclut les fichiers importés et le rapport actif.")
        print("Exécution : import refusé, annulation, descendants, délai, navigation après erreur et rétention vérifiés.")
    }
}

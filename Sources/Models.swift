import Foundation
import Combine
import PDFKit

struct Location: Decodable {
    let page: Int
    let rects: [[Double]]
    let precision: String
    let reason: String
}

struct Issue: Decodable, Identifiable {
    let id: String
    let clause: String
    let test: String
    let title: String
    let translated: Bool
    let advice: String
    let requirement: String
    let message: String
    let context: String
    let locations: [Location]
    var position: String {
        let pages = locations.map { String($0.page) }.joined(separator: ", ")
        return pages.isEmpty ? "Document · sans page précise" : "Page" + (locations.count > 1 ? "s " : " ") + pages
    }
}

struct RuleCoverage: Decodable {
    let clause: String
    let test: String
    let displayed: Int
    let total: Int
}

struct Inspection: Decodable {
    let profile: String
    let failedChecks: Int
    let passedChecks: Int
    let failedRules: Int
    let pageCount: Int
    let issues: [Issue]
    let pdfPath: String
    let pdfHash: String
    let reportPath: String
    let provenance: String
    let fresh: Bool
    let complete: Bool
    let coverage: [RuleCoverage]
}

struct WorkerError: Decodable { let error: String }

@MainActor
final class Inspector: ObservableObject {
    @Published var pdfURL: URL?
    @Published var inspection: Inspection?
    @Published var selectedID: String?
    @Published var page = 1
    @Published var busy = false
    @Published var error: String?
    @Published var query = ""
    @Published var zoom: CGFloat = 1
    @Published var fitRequest = UUID()
    @Published var documentGeneration = UUID()
    @Published var pageCount = 0
    @Published var notice: String?
    private var task: WorkerTask?
    var workerScript: URL? = Bundle.main.url(forResource: "analyzer", withExtension: "py")
    var pythonExecutable: String = Bundle.main.object(forInfoDictionaryKey: "PythonExecutable") as? String ?? "/opt/homebrew/bin/python3"
    var workerTimeout: TimeInterval = 180
    var reportFolder: URL = ReportCache.folder
    var selected: Issue? { inspection?.issues.first { $0.id == selectedID } }
    var currentLocation: Location? { selected?.locations.first { $0.page == page } }
    var filtered: [Issue] {
        (inspection?.issues ?? []).filter {
            query.isEmpty || "\($0.title) \($0.clause) \($0.position) \($0.message) \($0.requirement)".localizedCaseInsensitiveContains(query)
        }
    }
    func select(_ id: String?) {
        selectedID = id
        if let first = selected?.locations.first { page = first.page }
    }
    func adjustZoom() {
        zoom = 1
        fitRequest = UUID()
    }
    private func showInitialPDF(_ pdf: URL) {
        guard pdfURL == nil else { return }
        pdfURL = pdf
        pageCount = PDFDocument(url: pdf)?.pageCount ?? 0
        documentGeneration = UUID()
    }
    func run(pdf: URL, report: URL? = nil) {
        guard !busy else { return }
        error = nil
        notice = nil
        busy = true
        guard let script = workerScript else {
            error = "Le moteur de lecture manque dans l’application. Reconstruire le paquet."
            busy = false
            showInitialPDF(pdf)
            return
        }
        let folder = reportFolder
        var arguments = ["-B", script.path, "--pdf", pdf.path, "--output-dir", folder.path]
        if let report { arguments += ["--report", report.path] }
        let job = WorkerTask()
        task = job
        let python = pythonExecutable
        let timeout = workerTimeout
        DispatchQueue.global(qos: .userInitiated).async { [arguments] in
            do {
                let data = try job.run(executable: python, arguments: arguments, timeout: timeout)
                if let failure = try? JSONDecoder().decode(WorkerError.self, from: data) {
                    throw NSError(domain: "Inspecteur", code: 1, userInfo: [NSLocalizedDescriptionKey: failure.error])
                }
                let result = try JSONDecoder().decode(Inspection.self, from: data)
                DispatchQueue.main.async {
                    if let reason = job.stopReason {
                        self.error = reason
                        self.busy = false
                        self.task = nil
                        self.showInitialPDF(pdf)
                        return
                    }
                    self.pdfURL = pdf
                    self.documentGeneration = UUID()
                    self.pageCount = result.pageCount
                    self.page = 1
                    self.query = ""
                    self.inspection = result
                    self.busy = false
                    self.task = nil
                    self.select(result.issues.first?.id)
                    self.cleanReports()
                    #if INSPECTOR_DIAGNOSTICS
                    self.captureIfRequested()
                    #endif
                }
            } catch {
                DispatchQueue.main.async {
                    self.error = error is DecodingError ? "La réponse du moteur est incomplète ou illisible. Le résultat précédent est conservé." : error.localizedDescription
                    self.busy = false
                    self.task = nil
                    // Un échec initial laisse néanmoins le PDF consultable et navigable.
                    self.showInitialPDF(pdf)
                }
            }
        }
    }
    func cancel() { task?.stop() }
    func cleanReports(clear: Bool = false) {
        do {
            let count = try ReportCache.prune(folder: reportFolder, protecting: inspection.map { URL(fileURLWithPath: $0.reportPath) }, keep: clear ? 0 : 50)
            if count > 0 { notice = "\(count) ancien(s) rapport(s) déplacé(s) dans la Corbeille. Le rapport affiché est conservé." }
        } catch { notice = "Certains anciens rapports n’ont pas pu rejoindre la Corbeille. Ils sont conservés." }
    }
}

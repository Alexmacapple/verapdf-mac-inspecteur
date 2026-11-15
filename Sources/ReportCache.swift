import Foundation

/// Les rapports générés devenus anciens rejoignent la Corbeille, jamais les originaux importés.
enum ReportCache {
    static let folder = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        .appendingPathComponent("Inspecteur veraPDF/Rapports", isDirectory: true)

    static func prune(folder: URL = folder, protecting: URL?, now: Date = Date(),
                      keep: Int = 50, maxAge: TimeInterval = 30 * 86400,
                      recycle: (URL) throws -> Void = { try FileManager.default.trashItem(at: $0, resultingItemURL: nil) }) throws -> Int {
        let manager = FileManager.default
        guard manager.fileExists(atPath: folder.path) else { return 0 }
        let files = try manager.contentsOfDirectory(at: folder, includingPropertiesForKeys: [.contentModificationDateKey, .isRegularFileKey, .isSymbolicLinkKey])
            .filter { url in
                guard url.lastPathComponent.range(of: "^[0-9a-f]{12}-[0-9a-f]{12}\\.xml$", options: .regularExpression) != nil,
                      let info = try? url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey]) else { return false }
                return info.isRegularFile == true && info.isSymbolicLink != true
            }.sorted { date($0) > date($1) }
        var count = 0
        for (index, file) in files.enumerated() where file.standardizedFileURL != protecting?.standardizedFileURL {
            if index >= keep || now.timeIntervalSince(date(file)) > maxAge {
                try recycle(file)
                count += 1
            }
        }
        return count
    }
    private static func date(_ url: URL) -> Date {
        (try? url.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
    }
}

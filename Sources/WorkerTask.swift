import Foundation
import Darwin

/// Un traitement possède son processus et son délai ; aucun résultat annulé ne peut être livré.
final class WorkerTask: @unchecked Sendable {
    private let lock = NSLock()
    private var process: Process?
    private var stopped: String?
    var stopReason: String? {
        lock.lock()
        defer { lock.unlock() }
        return stopped
    }

    func stop(_ reason: String = "Analyse annulée. Le résultat précédent est conservé.") {
        lock.lock()
        if stopped == nil { stopped = reason }
        let running = process
        if let running, running.isRunning { signal(running, SIGTERM) }
        lock.unlock()
        DispatchQueue.global().asyncAfter(deadline: .now() + 2) { [weak self, weak running] in
            guard let self, let running else { return }
            self.lock.lock()
            if self.process === running && (running.isRunning || kill(-running.processIdentifier, 0) == 0) {
                self.signal(running, SIGKILL)
            }
            self.lock.unlock()
        }
    }

    private func signal(_ process: Process, _ signal: Int32) {
        let pid = process.processIdentifier
        // Le moteur ouvre une session POSIX avant de lancer veraPDF.
        if kill(-pid, signal) != 0 && process.isRunning { _ = kill(pid, signal) }
    }

    func run(executable: String, arguments: [String], timeout: TimeInterval = 180) throws -> Data {
        let child = Process()
        child.executableURL = URL(fileURLWithPath: executable)
        child.arguments = arguments
        let output = Pipe()
        child.standardOutput = output
        child.standardError = FileHandle.nullDevice
        lock.lock()
        if let stopped {
            lock.unlock()
            throw failure(stopped)
        }
        do { try child.run() }
        catch {
            lock.unlock()
            throw failure("Impossible de démarrer le moteur. Vérifier Python et les dépendances installées.")
        }
        process = child
        lock.unlock()
        let timer = DispatchSource.makeTimerSource(queue: .global())
        timer.schedule(deadline: .now() + timeout)
        timer.setEventHandler { [weak self] in self?.stop("Délai global dépassé (180 secondes). Le résultat précédent est conservé.") }
        timer.resume()
        defer { timer.cancel() }
        let data = output.fileHandleForReading.readDataToEndOfFile()
        child.waitUntilExit()
        lock.lock()
        let reason = stopped
        process = nil
        lock.unlock()
        if let reason { throw failure(reason) }
        if child.terminationStatus != 0, (try? JSONDecoder().decode(WorkerError.self, from: data)) == nil {
            throw failure("Le moteur s’est interrompu. Vérifier Python, pikepdf et PyMuPDF.")
        }
        return data
    }

    private func failure(_ message: String) -> NSError {
        NSError(domain: "Inspecteur", code: 1, userInfo: [NSLocalizedDescriptionKey: message])
    }
}

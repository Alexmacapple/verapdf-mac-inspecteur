import AppKit
import SwiftUI

struct InspectorView: View {
    @ObservedObject var model: Inspector
    var body: some View {
        VStack(spacing: 0) {
            if let message = model.error {
                Label(message, systemImage: "exclamationmark.triangle")
                    .foregroundStyle(.red).textSelection(.enabled).padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            if model.busy {
                HStack {
                    ProgressView().controlSize(.small)
                    Text("Contrôle PDF/UA-1 et repérage des erreurs…")
                    Spacer()
                    Button("Annuler", action: model.cancel).keyboardShortcut(.cancelAction)
                }
                    .padding().frame(maxWidth: .infinity, alignment: .leading)
            }
            if let result = model.inspection, !result.fresh {
                Label(result.provenance, systemImage: "info.circle")
                    .padding().frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.blue.opacity(0.08))
            }
            if let notice = model.notice {
                Text(notice).font(.callout).padding(.horizontal).padding(.vertical, 6)
            }
            if let result = model.inspection, !result.complete {
                VStack(alignment: .leading, spacing: 4) {
                    Label("Diagnostic incomplet : \(result.issues.count) occurrences chargées sur \(result.failedChecks) échecs.", systemImage: "exclamationmark.triangle")
                        .font(.headline)
                    Text("Le XML ou la limite locale de 2 000 occurrences ne permet pas de tout afficher. Consulter le rapport complet.")
                    ForEach(Array(result.coverage.filter { $0.displayed < $0.total }.enumerated()), id: \.offset) { _, rule in
                        Text("Règle \(rule.clause)-\(rule.test) : \(rule.displayed) / \(rule.total) occurrences chargées.")
                    }
                }.padding().frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.orange.opacity(0.15))
            }
            HSplitView {
                issueList.frame(minWidth: 255, idealWidth: 290, maxWidth: 380)
                preview.frame(minWidth: 400, maxWidth: .infinity, maxHeight: .infinity)
                detail.frame(minWidth: 300, idealWidth: 340, maxWidth: 440)
            }
            Divider()
            HStack {
                Text(model.inspection?.provenance ?? "Lecture locale · Aucun document modifié")
                Spacer()
                if let result = model.inspection {
                    Text("\(model.filtered.count) visibles · \(result.issues.count) chargées / \(result.failedChecks) échecs")
                }
            }.font(.caption).foregroundStyle(.secondary).padding(.horizontal, 14).padding(.vertical, 8)
        }
        .frame(minWidth: 1100, minHeight: 700)
        .background(Color(nsColor: .windowBackgroundColor))
        .toolbar {
            ToolbarItemGroup {
                Button(action: model.choosePDF) { Label("Ouvrir un PDF", systemImage: "doc.badge.plus") }
                    .keyboardShortcut("o").disabled(model.busy)
                Button { if let url = model.pdfURL { model.run(pdf: url) } } label: {
                    Label("Analyser", systemImage: "checkmark.magnifyingglass")
                }.disabled(model.pdfURL == nil || model.busy).help("Produire un rapport PDF/UA-1 sur le PDF ouvert")
                Button(action: model.chooseReport) { Label("Importer un XML", systemImage: "square.and.arrow.down") }
                    .disabled(model.pdfURL == nil || model.busy)
                Button(action: model.saveReport) { Label("Enregistrer le XML", systemImage: "square.and.arrow.up") }
                    .disabled(model.inspection == nil || model.busy)
                Menu {
                    Button("Ouvrir le dossier des rapports") {
                        try? FileManager.default.createDirectory(at: ReportCache.folder, withIntermediateDirectories: true)
                        NSWorkspace.shared.open(ReportCache.folder)
                    }
                    Button("Mettre les anciens rapports à la Corbeille") { model.cleanReports(clear: true) }
                } label: { Label("Rapports", systemImage: "folder") }
                    .disabled(model.busy)
                    .help("Le rapport affiché est conservé. Les XML enregistrés ailleurs ne sont pas concernés.")
            }
        }
        .navigationTitle(model.pdfURL?.lastPathComponent ?? "veraPDF Mac Inspecteur")
    }
    private var issueList: some View {
        VStack(alignment: .leading, spacing: 12) {
            VStack(alignment: .leading, spacing: 5) {
                Text("Erreurs à examiner").font(.title2.bold())
                if let report = model.inspection {
                    Text("\(report.failedRules) règles · \(report.failedChecks) échecs").foregroundStyle(.secondary)
                } else { Text("Un PDF et son contrôle PDF/UA-1").foregroundStyle(.secondary) }
            }.padding(.horizontal).padding(.top)
            TextField("Filtrer : figure, police, page…", text: $model.query)
                .textFieldStyle(.roundedBorder).padding(.horizontal)
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 4) {
                        ForEach(model.filtered) { issue in
                            Button { model.select(issue.id) } label: {
                                VStack(alignment: .leading, spacing: 5) {
                                    Text(issue.title).font(.headline)
                                    if !issue.translated {
                                        Text(issue.requirement).font(.subheadline).lineLimit(3)
                                    }
                                    Text(issue.position).font(.subheadline).foregroundStyle(.secondary)
                                    Text("\(issue.clause)-\(issue.test) · occurrence \((Int(issue.id) ?? 0)+1)")
                                        .font(.caption).foregroundStyle(.secondary)
                                    if model.selectedID == issue.id { Text("Sélectionnée").font(.caption.bold()) }
                                }.frame(maxWidth: .infinity, alignment: .leading).padding(12)
                                .background(model.selectedID == issue.id ? Color.accentColor.opacity(0.12) : Color.clear)
                                .clipShape(RoundedRectangle(cornerRadius: 6))
                            }.buttonStyle(.plain).id(issue.id)
                        }
                    }.padding(.horizontal, 8)
                }.onChange(of: model.selectedID) { _, value in if let value { proxy.scrollTo(value) } }
            }
            if model.inspection?.issues.isEmpty == true {
                Label("Aucun échec dans ce rapport", systemImage: "checkmark.circle").padding()
            } else if model.filtered.isEmpty && !model.query.isEmpty {
                Text("Aucune occurrence pour ce filtre.").foregroundStyle(.secondary).padding()
            }
        }
    }
    private var preview: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                Button { model.page = max(1, model.page-1) } label: { Image(systemName: "chevron.left") }
                    .accessibilityLabel("Page précédente").disabled(model.page <= 1)
                Text(model.pageCount > 0 ? "Page \(model.page) / \(model.pageCount)" : "Aucune page lisible").monospacedDigit()
                Button { model.page = min(max(1, model.pageCount), model.page+1) } label: { Image(systemName: "chevron.right") }
                    .accessibilityLabel("Page suivante").disabled(model.page >= model.pageCount)
                Spacer()
                Button { model.zoom = max(0.5, model.zoom-0.25) } label: { Image(systemName: "minus.magnifyingglass") }.accessibilityLabel("Réduire")
                Button("Ajuster") { model.zoom = 1 }
                Button { model.zoom = min(4, model.zoom+0.25) } label: { Image(systemName: "plus.magnifyingglass") }.accessibilityLabel("Agrandir")
            }.buttonStyle(.borderless).padding(12)
            Divider()
            if model.pdfURL != nil {
                PDFCanvas(url: model.pdfURL, generation: model.documentGeneration, page: $model.page,
                          zoom: model.zoom, rectangles: model.currentLocation?.rects ?? [])
            } else {
                VStack(spacing: 18) {
                    Image(systemName: "doc.text.magnifyingglass").font(.system(size: 48)).foregroundStyle(.secondary)
                    Text("Situer les corrections dans le PDF").font(.title2)
                    Text("Ouvrir un document, puis examiner ses erreurs\nsans changer son contenu.")
                        .foregroundStyle(.secondary).multilineTextAlignment(.center)
                    Button("Ouvrir un PDF", action: model.choosePDF).buttonStyle(.borderedProminent)
                }.frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }
    private var detail: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                if let issue = model.selected {
                    Text(issue.title).font(.title2.bold())
                    Label("PDF/UA-1 · \(issue.clause)-\(issue.test)", systemImage: "list.bullet.rectangle")
                        .font(.subheadline).foregroundStyle(.secondary)
                    section("Correction à préparer", issue.advice)
                    if !issue.translated {
                        section("Exigence originale · traduction indisponible", issue.requirement)
                    }
                    if issue.locations.isEmpty {
                        Label("Sans localisation dans une page", systemImage: "doc.text")
                        Text("Ce constat peut être global ou sa localisation reste inconnue. Aucun surlignage arbitraire n’est affiché.")
                            .foregroundStyle(.secondary)
                    } else {
                        Text("Localisation").font(.headline)
                        ForEach(Array(issue.locations.enumerated()), id: \.offset) { _, location in
                            Button("Afficher la page \(location.page)") { model.page = location.page }
                            Text(location.reason).font(.subheadline).foregroundStyle(.secondary)
                            Text(location.rects.isEmpty ? "Page connue · zone précise indisponible" :
                                 location.precision == "partial" ? "Localisation partielle · \(location.rects.count) zone(s), contenu supplémentaire non localisé" :
                                 "\(location.rects.count) zone(s) repérée(s)")
                                .font(.caption.bold())
                        }
                    }
                    Divider()
                    DisclosureGroup("Exigence et preuve technique") {
                        VStack(alignment: .leading, spacing: 12) {
                            Text(issue.requirement)
                            Text(issue.message)
                            Text(issue.context).font(.caption.monospaced())
                        }.padding(.top, 8).textSelection(.enabled)
                    }
                    Text("La correction s’effectue dans le document source ou un outil de remédiation. Cet inspecteur reste en lecture seule.")
                        .font(.caption).foregroundStyle(.secondary)
                } else {
                    Text("Le diagnostic").font(.title2.bold())
                    Text("Sélectionner une erreur pour lire le constat, préparer la correction et accéder aux pages concernées.")
                        .foregroundStyle(.secondary)
                    if let result = model.inspection, result.failedChecks == 0 {
                        Text("Aucun échec technique signalé. La pertinence des alternatives et l’usage réel du document restent à examiner humainement.")
                    }
                }
            }.padding(22).frame(maxWidth: .infinity, alignment: .leading).textSelection(.enabled)
        }
    }
    private func section(_ title: String, _ content: String) -> some View {
        VStack(alignment: .leading, spacing: 8) { Text(title).font(.headline); Text(content) }
    }
}

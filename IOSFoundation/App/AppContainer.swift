import Foundation
import SwiftData
import SwiftUI

struct AppContainer: Sendable {
    let configuration: AppConfiguration
    let httpClient: any HTTPClient
    let keyValueStore: any KeyValueStore
    let logger: any AppLogging

    static func live(configuration: AppConfiguration = .load()) -> AppContainer {
        AppContainer(
            configuration: configuration,
            httpClient: URLSessionHTTPClient(),
            keyValueStore: UserDefaultsStore(),
            logger: AppLogger(category: "application")
        )
    }

    static var preview: AppContainer {
        AppContainer(
            configuration: AppConfiguration(environmentValue: "development"),
            httpClient: URLSessionHTTPClient(),
            keyValueStore: UserDefaultsStore(suiteName: "preview"),
            logger: AppLogger(category: "preview")
        )
    }
}

struct EvidenceEditorSheet: View {
    let matter: Matter
    let importResult: EvidenceImportResult?
    let existingEvidence: [EvidenceRecord]

    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var modelContext
    @State private var title: String
    @State private var kind: EvidenceKind = .document
    @State private var eventDate = Date.now
    @State private var hasEventDate = false
    @State private var supports = ""
    @State private var limitations = ""
    @State private var notes = ""

    init(matter: Matter, importResult: EvidenceImportResult?, existingEvidence: [EvidenceRecord]) {
        self.matter = matter
        self.importResult = importResult
        self.existingEvidence = existingEvidence
        let filename = importResult?.originalFilename ?? ""
        _title = State(initialValue: URL(fileURLWithPath: filename).deletingPathExtension().lastPathComponent)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Evidence") {
                    TextField("Title", text: $title)
                    Picker("Type", selection: $kind) {
                        ForEach(EvidenceKind.allCases) { type in
                            Text(type.title).tag(type)
                        }
                    }
                    Toggle("Has event date", isOn: $hasEventDate)
                    if hasEventDate {
                        DatePicker(
                            "Event date",
                            selection: $eventDate,
                            displayedComponents: [.date, .hourAndMinute]
                        )
                    }
                }
                Section("Meaning") {
                    TextField("What this supports", text: $supports, axis: .vertical)
                    TextField("What this does not establish", text: $limitations, axis: .vertical)
                    TextField("Notes", text: $notes, axis: .vertical)
                }
                if let importResult {
                    Section("Original") {
                        LabeledContent("Filename", value: importResult.originalFilename)
                        Text(importResult.sha256)
                            .font(.caption2.monospaced())
                            .textSelection(.enabled)
                    }
                }
            }
            .navigationTitle("Add Evidence")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        if let path = importResult?.storedRelativePath {
                            EvidenceFileStore.removeImported(relativePath: path)
                        }
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { save() }
                        .disabled(title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
    }

    private func save() {
        var storedPath = importResult?.storedRelativePath
        var duplicateID: UUID?
        if let imported = importResult {
            if let duplicate = existingEvidence.first(where: { $0.sha256 == imported.sha256 }) {
                EvidenceFileStore.removeImported(relativePath: imported.storedRelativePath)
                storedPath = duplicate.storedRelativePath
                duplicateID = duplicate.id
            }
        }

        modelContext.insert(
            EvidenceRecord(
                matterID: matter.id,
                title: title.trimmingCharacters(in: .whitespacesAndNewlines),
                kind: kind,
                eventDate: hasEventDate ? eventDate : nil,
                originalFilename: importResult?.originalFilename,
                storedRelativePath: storedPath,
                sha256: importResult?.sha256,
                fileSize: importResult?.fileSize,
                notes: notes,
                supports: supports,
                limitations: limitations,
                isCanonical: duplicateID == nil,
                duplicateOfID: duplicateID
            )
        )
        matter.updatedAt = .now
        try? modelContext.save()
        dismiss()
    }
}

struct QuickAddSheet: View {
    let matter: Matter
    let kind: QuickAddKind

    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var modelContext
    @State private var title = ""
    @State private var detail = ""
    @State private var date = Date.now
    @State private var requestedFrom = ""
    @State private var trigger = ""

    var body: some View {
        NavigationStack {
            Form {
                TextField("Title", text: $title)
                if kind == .timeline || kind == .deadline {
                    DatePicker("Date", selection: $date)
                }
                if kind == .missing {
                    TextField("Requested from", text: $requestedFrom)
                }
                if kind == .deadline {
                    TextField("Trigger / basis", text: $trigger, axis: .vertical)
                } else {
                    TextField("Details", text: $detail, axis: .vertical)
                }
            }
            .navigationTitle("Add \(kind.title)")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { save() }
                        .disabled(title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
    }

    private func save() {
        let cleanTitle = title.trimmingCharacters(in: .whitespacesAndNewlines)
        switch kind {
        case .timeline:
            modelContext.insert(
                TimelineRecord(matterID: matter.id, date: date, title: cleanTitle, detail: detail)
            )
        case .issue:
            modelContext.insert(IssueRecord(matterID: matter.id, title: cleanTitle, detail: detail))
        case .missing:
            modelContext.insert(
                MissingEvidenceRecord(
                    matterID: matter.id,
                    title: cleanTitle,
                    detail: detail,
                    requestedFrom: requestedFrom
                )
            )
        case .deadline:
            modelContext.insert(
                DeadlineRecord(matterID: matter.id, title: cleanTitle, date: date, trigger: trigger)
            )
        }
        matter.updatedAt = .now
        try? modelContext.save()
        dismiss()
    }
}

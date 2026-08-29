import SwiftData
import SwiftUI
import UniformTypeIdentifiers

struct RootView: View {
    let environment: AppEnvironment
    let container: AppContainer

    @Environment(\.modelContext) private var modelContext
    @Query(sort: \Matter.updatedAt, order: .reverse) private var matters: [Matter]
    @State private var showingNewMatter = false

    var body: some View {
        NavigationStack {
            Group {
                if matters.isEmpty {
                    ContentUnavailableView {
                        Label("No Matters Yet", systemImage: "tray")
                            .accessibilityIdentifier("proofledger.empty.title")
                    } description: {
                        Text("Create a matter, then add evidence, events, issues, missing items, and deadlines.")
                    } actions: {
                        Button("New Matter") {
                            showingNewMatter = true
                        }
                        .buttonStyle(.borderedProminent)
                        .accessibilityIdentifier("proofledger.newMatter")
                    }
                } else {
                    List(matters) { matter in
                        NavigationLink {
                            MatterDetailView(matter: matter)
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(matter.title)
                                    .font(.headline)
                                Text(matter.updatedAt, format: .dateTime.day().month().year())
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .accessibilityIdentifier("proofledger.matter.\(matter.id.uuidString)")
                    }
                }
            }
            .navigationTitle("ProofLedger")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("New Matter", systemImage: "plus") {
                        showingNewMatter = true
                    }
                    .accessibilityIdentifier("proofledger.addMatter")
                }
            }
            .sheet(isPresented: $showingNewMatter) {
                NewMatterSheet { title in
                    modelContext.insert(Matter(title: title))
                    try? modelContext.save()
                }
            }
        }
        .accessibilityIdentifier("app.root")
    }
}

private struct NewMatterSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    let onSave: (String) -> Void

    var body: some View {
        NavigationStack {
            Form {
                TextField("Matter name", text: $title)
                    .textInputAutocapitalization(.sentences)
                    .accessibilityIdentifier("proofledger.matterName")
            }
            .navigationTitle("New Matter")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        onSave(title.trimmingCharacters(in: .whitespacesAndNewlines))
                        dismiss()
                    }
                    .disabled(title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    .accessibilityIdentifier("proofledger.saveMatter")
                }
            }
        }
    }
}

private enum MatterSection: String, CaseIterable, Identifiable {
    case evidence
    case timeline
    case issues
    case missing
    case deadlines

    var id: String {
        rawValue
    }

    var title: String {
        rawValue.capitalized
    }
}

enum QuickAddKind: String, Identifiable {
    case timeline
    case issue
    case missing
    case deadline

    var id: String {
        rawValue
    }

    var title: String {
        rawValue.capitalized
    }
}

private struct MatterDetailView: View {
    let matter: Matter

    @Query private var allEvidence: [EvidenceRecord]
    @Query private var allTimeline: [TimelineRecord]
    @Query private var allIssues: [IssueRecord]
    @Query private var allMissing: [MissingEvidenceRecord]
    @Query private var allDeadlines: [DeadlineRecord]

    @State private var section: MatterSection = .evidence
    @State private var showingImporter = false
    @State private var showingEvidenceEditor = false
    @State private var pendingImport: EvidenceImportResult?
    @State private var quickAddKind: QuickAddKind?
    @State private var showingImportError = false
    @State private var importErrorMessage = ""

    private var evidence: [EvidenceRecord] {
        allEvidence
            .filter { $0.matterID == matter.id }
            .sorted { ($0.eventDate ?? $0.importedAt) > ($1.eventDate ?? $1.importedAt) }
    }

    private var timeline: [TimelineRecord] {
        allTimeline.filter { $0.matterID == matter.id }.sorted { $0.date > $1.date }
    }

    private var issues: [IssueRecord] {
        allIssues.filter { $0.matterID == matter.id }
    }

    private var missing: [MissingEvidenceRecord] {
        allMissing.filter { $0.matterID == matter.id }
    }

    private var deadlines: [DeadlineRecord] {
        allDeadlines.filter { $0.matterID == matter.id }.sorted { $0.date < $1.date }
    }

    var body: some View {
        List {
            Section {
                Picker("Section", selection: $section) {
                    ForEach(MatterSection.allCases) { item in
                        Text(item.title).tag(item)
                    }
                }
                .pickerStyle(.menu)
                .accessibilityIdentifier("proofledger.sectionPicker")
            }

            switch section {
            case .evidence:
                evidenceContent
            case .timeline:
                timelineContent
            case .issues:
                issueContent
            case .missing:
                missingContent
            case .deadlines:
                deadlineContent
            }
        }
        .navigationTitle(matter.title)
        .toolbar { addMenu }
        .fileImporter(isPresented: $showingImporter, allowedContentTypes: [.item]) { result in
            switch result {
            case let .success(url):
                Task {
                    do {
                        pendingImport = try await Task.detached(priority: .userInitiated) {
                            try EvidenceFileStore.importOriginal(from: url)
                        }.value
                        showingEvidenceEditor = true
                    } catch {
                        importErrorMessage = error.localizedDescription
                        showingImportError = true
                    }
                }
            case let .failure(error):
                importErrorMessage = error.localizedDescription
                showingImportError = true
            }
        }
        .sheet(isPresented: $showingEvidenceEditor, onDismiss: { pendingImport = nil }) {
            EvidenceEditorSheet(
                matter: matter,
                importResult: pendingImport,
                existingEvidence: allEvidence
            )
        }
        .sheet(item: $quickAddKind) { kind in
            QuickAddSheet(matter: matter, kind: kind)
        }
        .alert("Import Failed", isPresented: $showingImportError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(importErrorMessage)
        }
    }

    @ToolbarContentBuilder
    private var addMenu: some ToolbarContent {
        ToolbarItem(placement: .topBarTrailing) {
            Menu("Add", systemImage: "plus") {
                Button("Import Original", systemImage: "square.and.arrow.down") {
                    showingImporter = true
                }
                Button("Evidence Record", systemImage: "doc.badge.plus") {
                    pendingImport = nil
                    showingEvidenceEditor = true
                }
                Divider()
                Button("Timeline Event", systemImage: "calendar.badge.plus") {
                    quickAddKind = .timeline
                }
                Button("Issue", systemImage: "exclamationmark.bubble") {
                    quickAddKind = .issue
                }
                Button("Missing Evidence", systemImage: "questionmark.folder") {
                    quickAddKind = .missing
                }
                Button("Deadline", systemImage: "clock.badge.exclamationmark") {
                    quickAddKind = .deadline
                }
            }
            .accessibilityIdentifier("proofledger.add")
        }
    }

    @ViewBuilder
    private var evidenceContent: some View {
        if evidence.isEmpty {
            Text("No evidence recorded.")
                .foregroundStyle(.secondary)
        } else {
            ForEach(evidence) { record in
                VStack(alignment: .leading, spacing: 6) {
                    Label(record.title, systemImage: record.kind.systemImage)
                        .font(.headline)
                    HStack {
                        Text(record.kind.title)
                        if record.duplicateOfID != nil {
                            Text("Duplicate")
                        }
                        if record.isCanonical {
                            Text("Canonical")
                        }
                    }
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    if let hash = record.sha256 {
                        Text("SHA-256  \(hash.prefix(16))…")
                            .font(.caption2.monospaced())
                            .foregroundStyle(.secondary)
                    }
                    if !record.supports.isEmpty {
                        Text("Supports: \(record.supports)")
                            .font(.subheadline)
                    }
                    if !record.limitations.isEmpty {
                        Text("Does not establish: \(record.limitations)")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 4)
            }
        }
    }

    @ViewBuilder
    private var timelineContent: some View {
        if timeline.isEmpty {
            Text("No timeline events recorded.").foregroundStyle(.secondary)
        } else {
            ForEach(timeline) { event in
                VStack(alignment: .leading, spacing: 4) {
                    Text(event.date, format: .dateTime.day().month().year())
                        .font(.caption.weight(.semibold))
                    Text(event.title).font(.headline)
                    if !event.detail.isEmpty {
                        Text(event.detail).foregroundStyle(.secondary)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var issueContent: some View {
        if issues.isEmpty {
            Text("No issues recorded.").foregroundStyle(.secondary)
        } else {
            ForEach(issues) { issue in
                LabeledContent(issue.title, value: issue.state.title)
            }
        }
    }

    @ViewBuilder
    private var missingContent: some View {
        if missing.isEmpty {
            Text("No missing evidence recorded.").foregroundStyle(.secondary)
        } else {
            ForEach(missing) { item in
                VStack(alignment: .leading, spacing: 4) {
                    LabeledContent(item.title, value: item.state.title)
                    if !item.requestedFrom.isEmpty {
                        Text("Requested from \(item.requestedFrom)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var deadlineContent: some View {
        if deadlines.isEmpty {
            Text("No deadlines recorded.").foregroundStyle(.secondary)
        } else {
            ForEach(deadlines) { deadline in
                VStack(alignment: .leading, spacing: 4) {
                    Text(deadline.date, format: .dateTime.day().month().year().hour().minute())
                        .font(.caption.weight(.semibold))
                    Text(deadline.title).font(.headline)
                    if !deadline.trigger.isEmpty {
                        Text("Trigger: \(deadline.trigger)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }
}

#Preview {
    RootView(environment: .live, container: .preview)
        .modelContainer(
            for: [
                Matter.self,
                EvidenceRecord.self,
                TimelineRecord.self,
                IssueRecord.self,
                MissingEvidenceRecord.self,
                DeadlineRecord.self,
            ],
            inMemory: true
        )
}

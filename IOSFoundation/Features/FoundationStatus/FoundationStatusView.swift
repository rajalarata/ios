import CryptoKit
import Foundation
import SwiftData

enum EvidenceKind: String, CaseIterable, Identifiable {
    case document
    case email
    case screenshot
    case photo
    case audio
    case message
    case letter
    case financial
    case other

    var id: String {
        rawValue
    }

    var title: String {
        rawValue.capitalized
    }

    var systemImage: String {
        switch self {
        case .document: "doc"
        case .email: "envelope"
        case .screenshot: "rectangle.inset.filled"
        case .photo: "photo"
        case .audio: "waveform"
        case .message: "message"
        case .letter: "mail"
        case .financial: "banknote"
        case .other: "archivebox"
        }
    }
}

enum VerificationState: String, CaseIterable, Identifiable {
    case unreviewed
    case verified
    case disputed

    var id: String {
        rawValue
    }

    var title: String {
        rawValue.capitalized
    }
}

enum TrackingState: String, CaseIterable, Identifiable {
    case open
    case waiting
    case resolved

    var id: String {
        rawValue
    }

    var title: String {
        rawValue.capitalized
    }
}

@Model
final class Matter {
    @Attribute(.unique) var id: UUID
    var title: String
    var createdAt: Date
    var updatedAt: Date

    init(title: String, now: Date = .now) {
        id = UUID()
        self.title = title
        createdAt = now
        updatedAt = now
    }
}

@Model
final class EvidenceRecord {
    @Attribute(.unique) var id: UUID
    var matterID: UUID
    var title: String
    var kindRawValue: String
    var eventDate: Date?
    var importedAt: Date
    var originalFilename: String?
    var storedRelativePath: String?
    var sha256: String?
    var fileSize: Int64?
    var notes: String
    var supports: String
    var limitations: String
    var verificationRawValue: String
    var isCanonical: Bool
    var duplicateOfID: UUID?

    init(
        matterID: UUID,
        title: String,
        kind: EvidenceKind,
        eventDate: Date?,
        importedAt: Date = .now,
        originalFilename: String? = nil,
        storedRelativePath: String? = nil,
        sha256: String? = nil,
        fileSize: Int64? = nil,
        notes: String = "",
        supports: String = "",
        limitations: String = "",
        verification: VerificationState = .unreviewed,
        isCanonical: Bool = true,
        duplicateOfID: UUID? = nil
    ) {
        id = UUID()
        self.matterID = matterID
        self.title = title
        kindRawValue = kind.rawValue
        self.eventDate = eventDate
        self.importedAt = importedAt
        self.originalFilename = originalFilename
        self.storedRelativePath = storedRelativePath
        self.sha256 = sha256
        self.fileSize = fileSize
        self.notes = notes
        self.supports = supports
        self.limitations = limitations
        verificationRawValue = verification.rawValue
        self.isCanonical = isCanonical
        self.duplicateOfID = duplicateOfID
    }

    var kind: EvidenceKind {
        EvidenceKind(rawValue: kindRawValue) ?? .other
    }

    var verification: VerificationState {
        VerificationState(rawValue: verificationRawValue) ?? .unreviewed
    }
}

@Model
final class TimelineRecord {
    @Attribute(.unique) var id: UUID
    var matterID: UUID
    var date: Date
    var title: String
    var detail: String
    var evidenceID: UUID?
    var verificationRawValue: String

    init(
        matterID: UUID,
        date: Date,
        title: String,
        detail: String = "",
        evidenceID: UUID? = nil,
        verification: VerificationState = .unreviewed
    ) {
        id = UUID()
        self.matterID = matterID
        self.date = date
        self.title = title
        self.detail = detail
        self.evidenceID = evidenceID
        verificationRawValue = verification.rawValue
    }

    var verification: VerificationState {
        VerificationState(rawValue: verificationRawValue) ?? .unreviewed
    }
}

@Model
final class IssueRecord {
    @Attribute(.unique) var id: UUID
    var matterID: UUID
    var title: String
    var detail: String
    var stateRawValue: String

    init(matterID: UUID, title: String, detail: String = "", state: TrackingState = .open) {
        id = UUID()
        self.matterID = matterID
        self.title = title
        self.detail = detail
        stateRawValue = state.rawValue
    }

    var state: TrackingState {
        TrackingState(rawValue: stateRawValue) ?? .open
    }
}

@Model
final class MissingEvidenceRecord {
    @Attribute(.unique) var id: UUID
    var matterID: UUID
    var title: String
    var detail: String
    var requestedFrom: String
    var requestedAt: Date?
    var followUpAt: Date?
    var stateRawValue: String

    init(
        matterID: UUID,
        title: String,
        detail: String = "",
        requestedFrom: String = "",
        requestedAt: Date? = nil,
        followUpAt: Date? = nil,
        state: TrackingState = .open
    ) {
        id = UUID()
        self.matterID = matterID
        self.title = title
        self.detail = detail
        self.requestedFrom = requestedFrom
        self.requestedAt = requestedAt
        self.followUpAt = followUpAt
        stateRawValue = state.rawValue
    }

    var state: TrackingState {
        TrackingState(rawValue: stateRawValue) ?? .open
    }
}

@Model
final class DeadlineRecord {
    @Attribute(.unique) var id: UUID
    var matterID: UUID
    var title: String
    var date: Date
    var trigger: String
    var verificationRawValue: String

    init(
        matterID: UUID,
        title: String,
        date: Date,
        trigger: String = "",
        verification: VerificationState = .unreviewed
    ) {
        id = UUID()
        self.matterID = matterID
        self.title = title
        self.date = date
        self.trigger = trigger
        verificationRawValue = verification.rawValue
    }

    var verification: VerificationState {
        VerificationState(rawValue: verificationRawValue) ?? .unreviewed
    }
}

struct EvidenceImportResult: Sendable {
    let originalFilename: String
    let storedRelativePath: String
    let sha256: String
    let fileSize: Int64
}

enum EvidenceFileStore {
    static func importOriginal(from sourceURL: URL, id: UUID = UUID()) throws -> EvidenceImportResult {
        let didAccess = sourceURL.startAccessingSecurityScopedResource()
        defer {
            if didAccess {
                sourceURL.stopAccessingSecurityScopedResource()
            }
        }

        let originalsDirectory = try originalsDirectory()
        let fileExtension = sourceURL.pathExtension
        let storedName = fileExtension.isEmpty ? id.uuidString : "\(id.uuidString).\(fileExtension)"
        let destinationURL = originalsDirectory.appendingPathComponent(storedName, isDirectory: false)

        try FileManager.default.copyItem(at: sourceURL, to: destinationURL)
        let hash = try sha256(for: destinationURL)
        let values = try destinationURL.resourceValues(forKeys: [.fileSizeKey])

        return EvidenceImportResult(
            originalFilename: sourceURL.lastPathComponent,
            storedRelativePath: storedName,
            sha256: hash,
            fileSize: Int64(values.fileSize ?? 0)
        )
    }

    static func sha256(for fileURL: URL) throws -> String {
        let handle = try FileHandle(forReadingFrom: fileURL)
        defer { try? handle.close() }

        var hasher = SHA256()
        while true {
            let data = try handle.read(upToCount: 1_048_576) ?? Data()
            guard !data.isEmpty else { break }
            hasher.update(data: data)
        }

        return hasher.finalize().map { String(format: "%02x", $0) }.joined()
    }

    static func removeImported(relativePath: String) {
        guard let directory = try? originalsDirectory() else { return }
        try? FileManager.default.removeItem(at: directory.appendingPathComponent(relativePath))
    }

    private static func originalsDirectory() throws -> URL {
        let applicationSupport = try FileManager.default.url(
            for: .applicationSupportDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
        let directory = applicationSupport
            .appendingPathComponent("ProofLedger", isDirectory: true)
            .appendingPathComponent("Originals", isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        return directory
    }
}

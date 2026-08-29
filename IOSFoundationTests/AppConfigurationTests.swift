import Foundation
import Testing
@testable import IOSFoundation

@Suite("App configuration")
struct AppConfigurationTests {
    @Test("Development is resolved explicitly")
    func resolvesDevelopment() {
        let configuration = AppConfiguration(environmentValue: "development")

        #expect(configuration.buildEnvironment == .development)
    }

    @Test("Production is resolved explicitly")
    func resolvesProduction() {
        let configuration = AppConfiguration(environmentValue: "production")

        #expect(configuration.buildEnvironment == .production)
    }

    @Test("Unknown values fail safe to development")
    func unknownValueFallsBackToDevelopment() {
        let configuration = AppConfiguration(environmentValue: "unexpected")

        #expect(configuration.buildEnvironment == .development)
    }
}

@Suite("ProofLedger records")
struct ProofLedgerRecordTests {
    @Test("Matter has stable creation timestamps")
    func matterCreation() {
        let now = Date(timeIntervalSince1970: 1_700_000_000)
        let matter = Matter(title: "Test matter", now: now)

        #expect(matter.title == "Test matter")
        #expect(matter.createdAt == now)
        #expect(matter.updatedAt == now)
    }

    @Test("Evidence preserves provenance fields")
    func evidenceProvenance() {
        let matterID = UUID()
        let evidence = EvidenceRecord(
            matterID: matterID,
            title: "Original email",
            kind: .email,
            eventDate: nil,
            originalFilename: "message.eml",
            sha256: "abc123",
            supports: "Transmission",
            limitations: "Opening or consideration"
        )

        #expect(evidence.matterID == matterID)
        #expect(evidence.kind == .email)
        #expect(evidence.originalFilename == "message.eml")
        #expect(evidence.supports == "Transmission")
        #expect(evidence.limitations == "Opening or consideration")
    }

    @Test("SHA-256 hashing is deterministic")
    func hashing() throws {
        let fileURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("proofledger-hash-test-\(UUID().uuidString)")
        try Data("proofledger".utf8).write(to: fileURL)
        defer { try? FileManager.default.removeItem(at: fileURL) }

        let digest = try EvidenceFileStore.sha256(for: fileURL)

        #expect(digest == "82c970775bd671215480d39aee1a251fa5d86ff4ceb140685756cf2f5e66b2a6")
    }
}

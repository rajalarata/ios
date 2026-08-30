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

@Suite("Authentication session")
struct AuthenticationSessionTests {
    private let now = Date(timeIntervalSince1970: 1_800_000_000)

    @Test("Current access token is returned without refresh")
    func currentToken() async throws {
        let tokens = AuthTokens(
            accessToken: "current-access",
            refreshToken: "refresh",
            expiresAt: now.addingTimeInterval(600)
        )
        let store = MemoryCredentialStore(tokens: tokens)
        let refresher = RecordingTokenRefresher(result: .success(tokens))
        let session = AuthenticationSession(store: store, refresher: refresher, now: { now })

        let accessToken = try await session.validAccessToken()

        #expect(accessToken == "current-access")
        #expect(await refresher.callCount == 0)
    }

    @Test("Expired access token refreshes and persists replacement")
    func expiredTokenRefreshes() async throws {
        let expired = AuthTokens(
            accessToken: "expired-access",
            refreshToken: "refresh-one",
            expiresAt: now.addingTimeInterval(-1)
        )
        let replacement = AuthTokens(
            accessToken: "replacement-access",
            refreshToken: "refresh-two",
            expiresAt: now.addingTimeInterval(900)
        )
        let store = MemoryCredentialStore(tokens: expired)
        let refresher = RecordingTokenRefresher(result: .success(replacement))
        let session = AuthenticationSession(store: store, refresher: refresher, now: { now })

        let accessToken = try await session.validAccessToken()

        #expect(accessToken == "replacement-access")
        #expect(await store.load() == replacement)
        #expect(await refresher.lastRefreshToken == "refresh-one")
    }

    @Test("Expired credentials without refresh token fail closed")
    func expiredWithoutRefreshFails() async {
        let expired = AuthTokens(
            accessToken: "expired-access",
            refreshToken: nil,
            expiresAt: now.addingTimeInterval(-1)
        )
        let store = MemoryCredentialStore(tokens: expired)
        let refresher = RecordingTokenRefresher(result: .failure(AuthenticationError.refreshUnavailable))
        let session = AuthenticationSession(store: store, refresher: refresher, now: { now })

        await #expect(throws: AuthenticationError.refreshUnavailable) {
            _ = try await session.validAccessToken()
        }
    }

    @Test("Sign out clears stored credentials")
    func signOutClearsCredentials() async throws {
        let tokens = AuthTokens(
            accessToken: "access",
            refreshToken: "refresh",
            expiresAt: now.addingTimeInterval(600)
        )
        let store = MemoryCredentialStore(tokens: tokens)
        let refresher = RecordingTokenRefresher(result: .success(tokens))
        let session = AuthenticationSession(store: store, refresher: refresher, now: { now })

        try await session.signOut()

        #expect(await store.load() == nil)
    }
}

actor MemoryCredentialStore: CredentialStore {
    private var tokens: AuthTokens?

    init(tokens: AuthTokens? = nil) {
        self.tokens = tokens
    }

    func load() -> AuthTokens? {
        tokens
    }

    func save(_ tokens: AuthTokens) {
        self.tokens = tokens
    }

    func clear() {
        tokens = nil
    }
}

actor RecordingTokenRefresher: TokenRefreshing {
    private let result: Result<AuthTokens, Error>
    private(set) var callCount = 0
    private(set) var lastRefreshToken: String?

    init(result: Result<AuthTokens, Error>) {
        self.result = result
    }

    func refresh(using refreshToken: String) throws -> AuthTokens {
        callCount += 1
        lastRefreshToken = refreshToken
        return try result.get()
    }
}

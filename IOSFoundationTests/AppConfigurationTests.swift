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
        let tokens = AuthTokens(accessToken: "current-access", refreshToken: "refresh", expiresAt: now.addingTimeInterval(600))
        let store = MemoryCredentialStore(tokens: tokens)
        let refresher = RecordingTokenRefresher(result: .success(tokens))
        let session = AuthenticationSession(store: store, refresher: refresher, now: { now })

        let accessToken = try await session.validAccessToken()

        #expect(accessToken == "current-access")
        #expect(await refresher.callCount == 0)
    }

    @Test("Expired access token refreshes and persists replacement")
    func expiredTokenRefreshes() async throws {
        let expired = AuthTokens(accessToken: "expired-access", refreshToken: "refresh-one", expiresAt: now.addingTimeInterval(-1))
        let replacement = AuthTokens(accessToken: "replacement-access", refreshToken: "refresh-two", expiresAt: now.addingTimeInterval(900))
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
        let expired = AuthTokens(accessToken: "expired-access", refreshToken: nil, expiresAt: now.addingTimeInterval(-1))
        let store = MemoryCredentialStore(tokens: expired)
        let refresher = RecordingTokenRefresher(result: .failure(AuthenticationError.refreshUnavailable))
        let session = AuthenticationSession(store: store, refresher: refresher, now: { now })

        await #expect(throws: AuthenticationError.refreshUnavailable) {
            _ = try await session.validAccessToken()
        }
    }

    @Test("Sign out clears stored credentials")
    func signOutClearsCredentials() async throws {
        let tokens = AuthTokens(accessToken: "access", refreshToken: "refresh", expiresAt: now.addingTimeInterval(600))
        let store = MemoryCredentialStore(tokens: tokens)
        let refresher = RecordingTokenRefresher(result: .success(tokens))
        let session = AuthenticationSession(store: store, refresher: refresher, now: { now })

        try await session.signOut()

        #expect(await store.load() == nil)
    }
}

@Suite("Authenticated HTTP client")
struct AuthenticatedHTTPClientTests {
    private let now = Date(timeIntervalSince1970: 1_800_000_000)

    @Test("Bearer token replaces any stale Authorization header")
    func bearerHeader() async throws {
        let tokens = AuthTokens(accessToken: "fresh-access", refreshToken: "refresh", expiresAt: now.addingTimeInterval(600))
        let store = MemoryCredentialStore(tokens: tokens)
        let refresher = RecordingTokenRefresher(result: .success(tokens))
        let session = AuthenticationSession(store: store, refresher: refresher, now: { now })
        let transport = RecordingHTTPClient(statuses: [200])
        let client = AuthenticatedHTTPClient(base: transport, session: session, allowedHosts: ["api.example.com"])
        var request = URLRequest(url: URL(string: "https://api.example.com/private")!)
        request.setValue("Bearer stale", forHTTPHeaderField: "Authorization")

        _ = try await client.data(for: request)

        let sent = await transport.requests
        #expect(sent.count == 1)
        #expect(sent[0].value(forHTTPHeaderField: "Authorization") == "Bearer fresh-access")
    }

    @Test("Credentials are never attached to an insecure request")
    func rejectsHTTP() async {
        let client = makeClient(statuses: [200])
        let request = URLRequest(url: URL(string: "http://api.example.com/private")!)

        await #expect(throws: AuthenticationError.insecureRequest) {
            _ = try await client.data(for: request)
        }
    }

    @Test("Credentials are restricted to approved hosts")
    func rejectsUnapprovedHost() async {
        let client = makeClient(statuses: [200])
        let request = URLRequest(url: URL(string: "https://evil.example/private")!)

        await #expect(throws: AuthenticationError.unapprovedHost) {
            _ = try await client.data(for: request)
        }
    }

    @Test("401 refreshes once and retries with replacement token")
    func refreshesAfter401() async throws {
        let current = AuthTokens(accessToken: "old-access", refreshToken: "refresh", expiresAt: now.addingTimeInterval(600))
        let replacement = AuthTokens(accessToken: "new-access", refreshToken: "refresh-2", expiresAt: now.addingTimeInterval(900))
        let store = MemoryCredentialStore(tokens: current)
        let refresher = RecordingTokenRefresher(result: .success(replacement))
        let session = AuthenticationSession(store: store, refresher: refresher, now: { now })
        let transport = RecordingHTTPClient(statuses: [401, 200])
        let client = AuthenticatedHTTPClient(base: transport, session: session, allowedHosts: ["api.example.com"])
        let request = URLRequest(url: URL(string: "https://api.example.com/private")!)

        _ = try await client.data(for: request)

        let sent = await transport.requests
        #expect(sent.count == 2)
        #expect(sent[0].value(forHTTPHeaderField: "Authorization") == "Bearer old-access")
        #expect(sent[1].value(forHTTPHeaderField: "Authorization") == "Bearer new-access")
        #expect(await refresher.callCount == 1)
    }

    @Test("Second 401 is surfaced without an authentication loop")
    func onlyRetriesOnce() async {
        let current = AuthTokens(accessToken: "old-access", refreshToken: "refresh", expiresAt: now.addingTimeInterval(600))
        let replacement = AuthTokens(accessToken: "new-access", refreshToken: "refresh-2", expiresAt: now.addingTimeInterval(900))
        let store = MemoryCredentialStore(tokens: current)
        let refresher = RecordingTokenRefresher(result: .success(replacement))
        let session = AuthenticationSession(store: store, refresher: refresher, now: { now })
        let transport = RecordingHTTPClient(statuses: [401, 401])
        let client = AuthenticatedHTTPClient(base: transport, session: session, allowedHosts: ["api.example.com"])
        let request = URLRequest(url: URL(string: "https://api.example.com/private")!)

        await #expect(throws: AppError.unexpectedHTTPStatus(401)) {
            _ = try await client.data(for: request)
        }

        #expect(await transport.requests.count == 2)
        #expect(await refresher.callCount == 1)
    }

    private func makeClient(statuses: [Int]) -> AuthenticatedHTTPClient {
        let tokens = AuthTokens(accessToken: "access", refreshToken: "refresh", expiresAt: now.addingTimeInterval(600))
        let store = MemoryCredentialStore(tokens: tokens)
        let refresher = RecordingTokenRefresher(result: .success(tokens))
        let session = AuthenticationSession(store: store, refresher: refresher, now: { now })
        return AuthenticatedHTTPClient(base: RecordingHTTPClient(statuses: statuses), session: session, allowedHosts: ["api.example.com"])
    }
}

actor MemoryCredentialStore: CredentialStore {
    private var tokens: AuthTokens?

    init(tokens: AuthTokens? = nil) {
        self.tokens = tokens
    }

    func load() -> AuthTokens? { tokens }
    func save(_ tokens: AuthTokens) { self.tokens = tokens }
    func clear() { tokens = nil }
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

actor RecordingHTTPClient: HTTPClient {
    private var statuses: [Int]
    private(set) var requests: [URLRequest] = []

    init(statuses: [Int]) {
        self.statuses = statuses
    }

    func data(for request: URLRequest) throws -> (Data, HTTPURLResponse) {
        requests.append(request)
        let status = statuses.isEmpty ? 200 : statuses.removeFirst()
        guard status != 401 else {
            throw AppError.unexpectedHTTPStatus(401)
        }
        let response = HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: nil, headerFields: nil)!
        return (Data(), response)
    }
}

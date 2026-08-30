import Foundation
import Security

protocol KeyValueStore: Sendable {
    func data(forKey key: String) async -> Data?
    func set(_ data: Data?, forKey key: String) async
}

actor UserDefaultsStore: KeyValueStore {
    private let defaults: UserDefaults

    init(suiteName: String? = nil) {
        if let suiteName, let defaults = UserDefaults(suiteName: suiteName) {
            self.defaults = defaults
        } else {
            defaults = .standard
        }
    }

    func data(forKey key: String) -> Data? {
        defaults.data(forKey: key)
    }

    func set(_ data: Data?, forKey key: String) {
        defaults.set(data, forKey: key)
    }
}

struct AuthTokens: Codable, Equatable, Sendable {
    let accessToken: String
    let refreshToken: String?
    let expiresAt: Date
}

protocol CredentialStore: Sendable {
    func load() async throws -> AuthTokens?
    func save(_ tokens: AuthTokens) async throws
    func clear() async throws
}

protocol TokenRefreshing: Sendable {
    func refresh(using refreshToken: String) async throws -> AuthTokens
}

enum AuthenticationError: Error, Equatable, Sendable {
    case missingCredentials
    case refreshUnavailable
    case invalidCredentialData
    case keychainFailure(OSStatus)
    case insecureRequest
    case unapprovedHost
}

struct KeychainCredentialStore: CredentialStore, Sendable {
    private let service: String
    private let account: String
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()

    init(
        service: String = Bundle.main.bundleIdentifier ?? "com.rajalarata.ios",
        account: String = "authentication.tokens"
    ) {
        self.service = service
        self.account = account
    }

    func load() async throws -> AuthTokens? {
        var query = baseQuery
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne

        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        if status == errSecItemNotFound {
            return nil
        }
        guard status == errSecSuccess else {
            throw AuthenticationError.keychainFailure(status)
        }
        guard let data = result as? Data else {
            throw AuthenticationError.invalidCredentialData
        }

        do {
            return try decoder.decode(AuthTokens.self, from: data)
        } catch {
            throw AuthenticationError.invalidCredentialData
        }
    }

    func save(_ tokens: AuthTokens) async throws {
        let data = try encoder.encode(tokens)
        let attributes: [String: Any] = [
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
        ]
        let status = SecItemUpdate(baseQuery as CFDictionary, attributes as CFDictionary)

        if status == errSecItemNotFound {
            var item = baseQuery
            attributes.forEach { item[$0.key] = $0.value }
            let addStatus = SecItemAdd(item as CFDictionary, nil)
            guard addStatus == errSecSuccess else {
                throw AuthenticationError.keychainFailure(addStatus)
            }
            return
        }

        guard status == errSecSuccess else {
            throw AuthenticationError.keychainFailure(status)
        }
    }

    func clear() async throws {
        let status = SecItemDelete(baseQuery as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw AuthenticationError.keychainFailure(status)
        }
    }

    private var baseQuery: [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
    }
}

actor AuthenticationSession {
    private let store: any CredentialStore
    private let refresher: any TokenRefreshing
    private let now: @Sendable () -> Date
    private let expiryLeeway: TimeInterval

    init(
        store: any CredentialStore,
        refresher: any TokenRefreshing,
        expiryLeeway: TimeInterval = 30,
        now: @escaping @Sendable () -> Date = { Date() }
    ) {
        self.store = store
        self.refresher = refresher
        self.expiryLeeway = expiryLeeway
        self.now = now
    }

    func validAccessToken(forceRefresh: Bool = false) async throws -> String {
        guard let tokens = try await store.load() else {
            throw AuthenticationError.missingCredentials
        }

        if !forceRefresh, tokens.expiresAt.timeIntervalSince(now()) > expiryLeeway {
            return tokens.accessToken
        }

        guard let refreshToken = tokens.refreshToken, !refreshToken.isEmpty else {
            throw AuthenticationError.refreshUnavailable
        }

        let replacement = try await refresher.refresh(using: refreshToken)
        try await store.save(replacement)
        return replacement.accessToken
    }

    func signOut() async throws {
        try await store.clear()
    }
}

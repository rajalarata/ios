import Foundation

protocol HTTPClient: Sendable {
    func data(for request: URLRequest) async throws -> (Data, HTTPURLResponse)
}

struct URLSessionHTTPClient: HTTPClient {
    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    func data(for request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        let (data, response) = try await session.data(for: request)

        guard let response = response as? HTTPURLResponse else {
            throw AppError.invalidResponse
        }

        guard 200 ..< 300 ~= response.statusCode else {
            throw AppError.unexpectedHTTPStatus(response.statusCode)
        }

        return (data, response)
    }
}

struct AuthenticatedHTTPClient: HTTPClient {
    private let base: any HTTPClient
    private let session: AuthenticationSession
    private let allowedHosts: Set<String>

    init(base: any HTTPClient, session: AuthenticationSession, allowedHosts: Set<String>) {
        self.base = base
        self.session = session
        self.allowedHosts = Set(allowedHosts.map { $0.lowercased() })
    }

    func data(for request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        try validateDestination(request)

        var authenticatedRequest = request
        let accessToken = try await session.validAccessToken()
        authenticatedRequest.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        do {
            return try await base.data(for: authenticatedRequest)
        } catch AppError.unexpectedHTTPStatus(401) {
            let replacementToken = try await session.validAccessToken(forceRefresh: true)
            authenticatedRequest.setValue("Bearer \(replacementToken)", forHTTPHeaderField: "Authorization")
            return try await base.data(for: authenticatedRequest)
        }
    }

    private func validateDestination(_ request: URLRequest) throws {
        guard let url = request.url, url.scheme?.lowercased() == "https" else {
            throw AuthenticationError.insecureRequest
        }
        guard let host = url.host?.lowercased(), allowedHosts.contains(host) else {
            throw AuthenticationError.unapprovedHost
        }
    }
}

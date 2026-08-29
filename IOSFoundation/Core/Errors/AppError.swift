enum AppError: Error, Equatable, Sendable {
    case invalidResponse
    case unexpectedHTTPStatus(Int)
}

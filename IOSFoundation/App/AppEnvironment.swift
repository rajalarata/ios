import Foundation

enum AppEnvironment: Equatable, Sendable {
    case live
    case uiTesting

    static func resolve(arguments: [String] = ProcessInfo.processInfo.arguments) -> AppEnvironment {
        arguments.contains("--ui-testing") ? .uiTesting : .live
    }

    var logValue: String {
        switch self {
        case .live:
            "live"
        case .uiTesting:
            "ui-testing"
        }
    }
}

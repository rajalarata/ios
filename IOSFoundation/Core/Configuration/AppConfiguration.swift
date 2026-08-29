import Foundation

struct AppConfiguration: Equatable, Sendable {
    enum BuildEnvironment: String, Equatable, Sendable {
        case development
        case production

        var displayName: String {
            rawValue.capitalized
        }
    }

    let buildEnvironment: BuildEnvironment

    init(environmentValue: String?) {
        buildEnvironment = BuildEnvironment(rawValue: environmentValue ?? "") ?? .development
    }

    static func load(bundle: Bundle = .main) -> AppConfiguration {
        AppConfiguration(
            environmentValue: bundle.object(forInfoDictionaryKey: "APP_CONFIGURATION") as? String
        )
    }
}

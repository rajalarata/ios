struct AppContainer: Sendable {
    let configuration: AppConfiguration
    let httpClient: any HTTPClient
    let keyValueStore: any KeyValueStore
    let logger: any AppLogging

    static func live(configuration: AppConfiguration = .load()) -> AppContainer {
        AppContainer(
            configuration: configuration,
            httpClient: URLSessionHTTPClient(),
            keyValueStore: UserDefaultsStore(),
            logger: AppLogger(category: "application")
        )
    }

    static var preview: AppContainer {
        AppContainer(
            configuration: AppConfiguration(environmentValue: "development"),
            httpClient: URLSessionHTTPClient(),
            keyValueStore: UserDefaultsStore(suiteName: "preview"),
            logger: AppLogger(category: "preview")
        )
    }
}

import SwiftUI

@main
struct IOSFoundationApp: App {
    private let environment: AppEnvironment
    private let container: AppContainer

    init() {
        let environment = AppEnvironment.resolve()
        let container = AppContainer.live()
        self.environment = environment
        self.container = container

        let buildEnvironment = container.configuration.buildEnvironment.rawValue
        let launchMode = environment.logValue
        container.logger.info("Application configured for \(buildEnvironment); launch mode: \(launchMode)")
    }

    var body: some Scene {
        WindowGroup {
            RootView(environment: environment, container: container)
        }
    }
}

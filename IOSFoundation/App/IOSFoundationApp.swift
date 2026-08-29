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

        container.logger.info(
            "Application configured for \(container.configuration.buildEnvironment.rawValue); launch mode: \(environment.logValue)"
        )
    }

    var body: some Scene {
        WindowGroup {
            RootView(environment: environment, container: container)
        }
    }
}

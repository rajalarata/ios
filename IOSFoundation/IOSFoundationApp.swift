import SwiftUI

@main
struct IOSFoundationApp: App {
    private let environment = AppEnvironment.resolve()

    var body: some Scene {
        WindowGroup {
            RootView(environment: environment)
        }
    }
}

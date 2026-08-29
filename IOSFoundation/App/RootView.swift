import SwiftUI

struct RootView: View {
    let environment: AppEnvironment
    let container: AppContainer

    var body: some View {
        NavigationStack {
            FoundationStatusView(configuration: container.configuration)
        }
        .accessibilityIdentifier("app.root")
    }
}

#Preview {
    RootView(
        environment: .live,
        container: .preview
    )
}

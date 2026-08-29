import SwiftUI

struct RootView: View {
    let environment: AppEnvironment

    var body: some View {
        NavigationStack {
            ContentUnavailableView(
                "Foundation Ready",
                systemImage: "checkmark.seal",
                description: Text("Native SwiftUI project, tests, and CI are configured.")
            )
            .navigationTitle("iOS Foundation")
        }
        .accessibilityIdentifier("root.foundation")
    }
}

#Preview {
    RootView(environment: .live)
}

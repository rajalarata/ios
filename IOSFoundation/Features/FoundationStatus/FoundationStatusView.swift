import SwiftUI

struct FoundationStatusView: View {
    let configuration: AppConfiguration

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "checkmark.seal")
                .font(.largeTitle)
                .accessibilityHidden(true)

            Text("Foundation Ready")
                .font(.title2.weight(.semibold))
                .multilineTextAlignment(.center)
                .accessibilityIdentifier("foundation.status.title")

            Text("Native SwiftUI project, tests, and CI are configured.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
                .accessibilityIdentifier("foundation.status.detail")

            Text(configuration.buildEnvironment.displayName)
                .font(.caption)
                .foregroundStyle(.secondary)
                .accessibilityLabel("Build configuration")
                .accessibilityValue(configuration.buildEnvironment.displayName)
                .accessibilityIdentifier("foundation.environment")
        }
        .padding()
        .navigationTitle("iOS Foundation")
    }
}

#Preview {
    NavigationStack {
        FoundationStatusView(
            configuration: AppConfiguration(environmentValue: "development")
        )
    }
}

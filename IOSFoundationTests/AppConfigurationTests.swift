import Testing
@testable import IOSFoundation

@Suite("App configuration")
struct AppConfigurationTests {
    @Test("Development is resolved explicitly")
    func resolvesDevelopment() {
        let configuration = AppConfiguration(environmentValue: "development")

        #expect(configuration.buildEnvironment == .development)
    }

    @Test("Production is resolved explicitly")
    func resolvesProduction() {
        let configuration = AppConfiguration(environmentValue: "production")

        #expect(configuration.buildEnvironment == .production)
    }

    @Test("Unknown values fail safe to development")
    func unknownValueFallsBackToDevelopment() {
        let configuration = AppConfiguration(environmentValue: "unexpected")

        #expect(configuration.buildEnvironment == .development)
    }
}

import Testing
@testable import IOSFoundation

@Suite("App environment")
struct AppEnvironmentTests {
    @Test("Defaults to live")
    func defaultsToLive() {
        #expect(AppEnvironment.resolve(arguments: ["IOSFoundation"]) == .live)
    }

    @Test("Recognizes UI testing launch argument")
    func recognizesUITesting() {
        #expect(AppEnvironment.resolve(arguments: ["IOSFoundation", "--ui-testing"]) == .uiTesting)
    }
}

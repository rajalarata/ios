import XCTest

final class IOSFoundationUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    func testFoundationScreenLaunches() throws {
        let app = XCUIApplication()
        app.launchArguments += ["--ui-testing"]
        app.launch()

        XCTAssertTrue(app.staticTexts["Foundation Ready"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.navigationBars["iOS Foundation"].exists)
    }
}

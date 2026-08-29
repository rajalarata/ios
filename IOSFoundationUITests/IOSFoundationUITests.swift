import XCTest

final class IOSFoundationUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    func testFoundationScreenLaunches() {
        let app = makeApplication()
        app.launch()

        let title = app.staticTexts["foundation.status.title"]
        XCTAssertTrue(title.waitForExistence(timeout: 5))
        XCTAssertEqual(title.label, "Foundation Ready")
        XCTAssertTrue(app.staticTexts["foundation.status.detail"].exists)
        XCTAssertTrue(app.staticTexts["foundation.environment"].exists)
        XCTAssertTrue(app.navigationBars["iOS Foundation"].exists)
    }

    @MainActor
    func testFoundationScreenAtAccessibilityTextSize() {
        let app = makeApplication(
            additionalArguments: [
                "-UIPreferredContentSizeCategoryName",
                "UICTContentSizeCategoryAccessibilityExtraExtraExtraLarge",
            ]
        )
        app.launch()

        XCTAssertTrue(app.staticTexts["foundation.status.title"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["foundation.status.detail"].exists)
    }

    @MainActor
    private func makeApplication(additionalArguments: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing"] + additionalArguments
        return app
    }
}

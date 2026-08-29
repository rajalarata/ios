import XCTest

final class IOSFoundationUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    func testProofLedgerCreatesMatter() {
        let app = makeApplication()
        app.launch()

        XCTAssertTrue(app.navigationBars["ProofLedger"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["proofledger.empty.title"].exists)

        app.buttons["proofledger.newMatter"].tap()
        let nameField = app.textFields["proofledger.matterName"]
        XCTAssertTrue(nameField.waitForExistence(timeout: 3))
        nameField.tap()
        nameField.typeText("Evidence Review")
        app.buttons["proofledger.saveMatter"].tap()

        XCTAssertTrue(app.staticTexts["Evidence Review"].waitForExistence(timeout: 3))
    }

    @MainActor
    func testProofLedgerAtAccessibilityTextSize() {
        let app = makeApplication(
            additionalArguments: [
                "-UIPreferredContentSizeCategoryName",
                "UICTContentSizeCategoryAccessibilityExtraExtraExtraLarge",
            ]
        )
        app.launch()

        XCTAssertTrue(app.navigationBars["ProofLedger"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["proofledger.newMatter"].exists)
    }

    @MainActor
    private func makeApplication(additionalArguments: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing"] + additionalArguments
        return app
    }
}

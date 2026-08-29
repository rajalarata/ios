# iOS

Production-quality native iOS foundation. The product concept is intentionally undefined at this stage.

## Baseline

- Swift and SwiftUI only for application code.
- Swift 6 language mode.
- iPhone deployment target: iOS 18.0.
- Xcode project committed to source control; no project-generator dependency.
- Swift Testing for unit tests and XCTest/XCUIAutomation for UI smoke tests.
- GitHub Actions on GitHub-hosted macOS runners for simulator builds and tests.
- Simulator CI does not require Apple signing credentials.

## Repository layout

```text
IOSFoundation.xcodeproj/   Xcode project and shared scheme
IOSFoundation/             Application source
IOSFoundationTests/        Unit tests
IOSFoundationUITests/      UI smoke tests
.github/workflows/         CI
```

## CI

`.github/workflows/ci.yml` runs on pushes, pull requests, and manual dispatch. It selects the repository's pinned Xcode version, runs the full Debug test suite with code coverage, then compiles the Release configuration for an iOS Simulator destination. Warnings are treated as errors in CI.

The workflow has read-only repository permissions and contains no signing material or other secrets.

## Signing and distribution

Development and CI remain signing-free until device installation or distribution is needed. Apple Developer account credentials, certificates, provisioning profiles, App Store Connect keys, and similar private material must never be committed. When distribution work begins, credentials will be supplied only through GitHub Actions secrets or Apple's authenticated tooling.

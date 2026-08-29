# iOS Foundation

Production-oriented native iOS baseline for the future application. The final product concept is intentionally undefined.

## Platform baseline

- Swift 6 language mode with complete strict concurrency checking.
- SwiftUI app lifecycle and `NavigationStack` composition root.
- Minimum deployment target: iOS 18.0.
- Stable CI: Xcode 26.6 on GitHub-hosted `macos-26` runners.
- Forward-compatibility CI: non-blocking Xcode 27 preview testing against iOS 27.
- Unit tests: Swift Testing.
- UI/accessibility smoke tests: XCTest and XCUIAutomation.
- No third-party runtime dependencies.

An iOS 18 deployment target remains compatible with later OS releases, while avoiding an unnecessary requirement that all future users run the newest iOS version.

## Architecture

```text
IOSFoundation/
├── App/                 # App lifecycle, composition root, launch environment
├── Core/                # Configuration, errors, logging
├── Features/            # Product-facing feature modules
├── Services/            # Networking and persistence boundaries
└── Resources/           # Future assets/localization/resources
```

`AppContainer` is the dependency injection boundary. Networking uses `URLSession` behind `HTTPClient`; persistence uses an actor-backed `UserDefaultsStore` behind `KeyValueStore`; logging uses unified logging behind `AppLogging`.

## Configuration

`Configuration/Debug.xcconfig` and `Configuration/Release.xcconfig` define only non-secret build configuration. The generated Info.plist receives `APP_CONFIGURATION` as `development` or `production`.

Never put credentials in `.xcconfig` files. Signing material and secrets belong in GitHub Secrets or Apple-managed credentials when distribution is configured.

## CI

`.github/workflows/ci.yml` contains required stable quality gates:

- SwiftFormat lint mode.
- SwiftLint strict mode.
- repository secret/signing-file hygiene checks.
- Swift Testing on iOS 26.2 and iOS 26.5 simulators.
- code coverage summaries using Apple's `xccov` tooling.
- UI and accessibility smoke tests on the iPhone 12 mini form factor when that simulator type is available.
- Release simulator compilation.
- failed `.xcresult` bundles retained for diagnostics.

Swift package caching is enabled only when a `Package.resolved` exists, so the repository does not maintain meaningless DerivedData caches while there are no external packages.

`.github/workflows/forward-compatibility.yml` exercises the full test suite with the `xcode-27` preview runner and iOS 27. It is deliberately non-blocking because GitHub marks that runner image as preview.

`.github/workflows/release.yml` validates that a Release device archive can be produced without signing. Distribution signing and TestFlight/App Store upload are intentionally absent until Apple credentials are available.

## Dependency policy

The default is Apple-native frameworks. A Swift package should be added only when it provides clear value that is not reasonably available from the platform, has an acceptable maintenance/security posture, and is isolated behind an application-owned interface where practical.

Dependabot monitors GitHub Actions references. Third-party actions are pinned to immutable commit SHAs.

## Repository governance

The repository includes CODEOWNERS, pull-request and issue templates, a security policy, and contributing rules. Repository rulesets/branch protection are a GitHub repository setting rather than source code; source-level policy files are committed here, while enforcement must be enabled through repository administration capabilities.

## Signing and distribution

No Apple certificate, provisioning profile, private key, App Store Connect key, or team credential is committed. Simulator CI does not require signing. The release workflow produces only an unsigned validation archive until distribution credentials are configured securely.

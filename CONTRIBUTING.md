# Contributing

This repository intentionally starts from a product-neutral native iOS foundation.

## Engineering rules

1. Keep the application native Swift and SwiftUI unless a reviewed requirement proves otherwise.
2. Prefer Apple platform APIs before adding external dependencies.
3. Keep dependencies injectable at architectural boundaries so tests do not require network, persistence, or production services.
4. Keep `main` buildable in Debug and Release with stable CI green.
5. Add Swift Testing coverage for logic and XCTest/XCUIAutomation coverage for user-facing flows.
6. Treat accessibility and compact iPhone layouts as baseline requirements.
7. Do not commit secrets, signing files, provisioning profiles, private certificates, or developer-specific configuration.
8. Update documentation when deployment targets, capabilities, privacy behavior, or release requirements change.

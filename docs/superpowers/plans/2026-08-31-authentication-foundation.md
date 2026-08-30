# Authentication Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add secure, provider-neutral token storage and authenticated HTTP request handling to ProofLedger without committing secrets or assuming a backend vendor.

**Architecture:** Keep the existing `HTTPClient` transport boundary, add actor-isolated token lifecycle management, store credentials only in Keychain, and decorate HTTP requests with authentication only for explicitly approved HTTPS hosts. Provider-specific sign-in and refresh networking stays behind protocols until a real backend is chosen.

**Tech Stack:** Swift 6, Foundation, Security.framework, Swift Testing, URLSession, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-31-authentication-foundation-design.md`

## Global Constraints

- Minimum deployment target remains iOS 18.0.
- Swift 6 complete strict concurrency remains enabled.
- Apple-native frameworks only; no runtime dependency is added.
- Never commit credentials, tokens, private keys, signing material, or provider client secrets.
- Tokens must never be persisted in UserDefaults or emitted to logs.
- Authenticated requests must be HTTPS and restricted to an explicit host allow-list.
- A 401 retry is limited to one forced refresh and one retry.

---

### Task 1: Token lifecycle tests

**Files:**
- Modify: `IOSFoundationTests/AppConfigurationTests.swift`
- Modify: `IOSFoundation.xcodeproj/project.pbxproj` only if production sources are added as separate files.

**Interfaces:**
- Produces expected APIs: `AuthTokens`, `CredentialStore`, `TokenRefreshing`, `AuthenticationSession`.

- [ ] Add tests proving a current token is returned unchanged, an expired token refreshes and persists, missing refresh capability fails closed, and sign-out clears credentials.
- [ ] Push the test-only commit to `auth-foundation`.
- [ ] Run GitHub Actions for the commit and confirm the unit-test build fails because the auth production types do not exist.

### Task 2: Secure credential storage and session

**Files:**
- Create or integrate focused production source for token/session types under `IOSFoundation/Services`.
- Modify: `IOSFoundation.xcodeproj/project.pbxproj` if needed.

**Interfaces:**
- `struct AuthTokens: Codable, Equatable, Sendable`
- `protocol CredentialStore: Sendable { func load() async throws -> AuthTokens?; func save(_:) async throws; func clear() async throws }`
- `protocol TokenRefreshing: Sendable { func refresh(using:) async throws -> AuthTokens }`
- `actor AuthenticationSession` exposing valid-token, forced-refresh, and sign-out operations.

- [ ] Implement Keychain persistence using Security.framework and `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`.
- [ ] Implement actor-isolated token validity and refresh behavior.
- [ ] Run the same tests and confirm they pass before continuing.

### Task 3: Authenticated HTTP decorator tests and implementation

**Files:**
- Modify: `IOSFoundation/Services/Networking/HTTPClient.swift` or add a focused networking source.
- Modify: `IOSFoundationTests/AppConfigurationTests.swift`.
- Modify: `IOSFoundation.xcodeproj/project.pbxproj` if needed.

**Interfaces:**
- Produce `AuthenticatedHTTPClient` implementing `HTTPClient`.

- [ ] Add tests for Bearer header replacement, HTTPS enforcement, host allow-list enforcement, one-time 401 refresh, and replacement-token retry.
- [ ] Confirm the new tests fail before implementation.
- [ ] Implement the minimum decorator behavior needed to pass those tests.
- [ ] Run the full stable unit-test matrix.

### Task 4: CI and documentation hardening

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `SECURITY.md`

- [ ] Add `persist-credentials: false` to every checkout in stable CI.
- [ ] Extend repository hygiene checks for obvious private-key/credential assignment patterns without printing secret values.
- [ ] Document the authentication component graph, request flow, Keychain policy, and future provider integration boundary.
- [ ] Run CI, lint, unit tests, UI smoke tests, and release validation through GitHub Actions.

### Task 5: Review and PR

- [ ] Review the branch diff against the design spec.
- [ ] Verify no credential values or signing material are introduced.
- [ ] Confirm required GitHub Actions checks are green on the final commit.
- [ ] Open a pull request from `auth-foundation` into `main` with implementation and verification details.

# Authentication Foundation Design

## Purpose

Add a production-oriented, provider-neutral authentication foundation to ProofLedger without inventing a backend, committing credentials, or coupling the application to a third-party identity vendor.

## Constraints

- iOS 18.0 minimum deployment target.
- Swift 6 with complete strict concurrency checking.
- Apple-native frameworks only.
- No credentials, tokens, signing keys, client secrets, or private keys in source control, build settings, logs, or UserDefaults.
- Authentication remains backend/provider-neutral until a real identity service is selected.
- Existing unauthenticated HTTPClient behavior remains available.

## Components

### AuthTokens

A Sendable/Codable value containing an access token, optional refresh token, and access-token expiry date. Token values are never logged.

### CredentialStore

An async protocol for loading, saving, and clearing AuthTokens. The live implementation uses the iOS Keychain with `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`. Tests use an in-memory implementation.

### TokenRefreshing

A provider-neutral protocol whose only responsibility is exchanging a refresh token for new AuthTokens. There is no concrete network implementation until a real backend exists.

### AuthenticationSession

An actor that owns token lifecycle. It returns a valid access token, refreshes an expired token when a refresh token is available, persists refreshed credentials, and clears credentials on sign-out. Refresh is centralized in the actor so concurrent callers do not directly manipulate stored credentials.

### AuthenticatedHTTPClient

A decorator around HTTPClient. For HTTPS requests to an explicitly allowed host it obtains a valid token, overwrites any existing Authorization header with a Bearer token, sends the request, and retries at most once after HTTP 401 if forced refresh succeeds. It refuses to attach credentials to non-HTTPS URLs or unapproved hosts.

The underlying HTTP transport needs to expose HTTP status responses to the decorator. `URLSessionHTTPClient` therefore continues to validate the response type but leaves status-policy decisions to a configurable wrapper. Existing call sites can keep the current `HTTPClient` success-only semantics.

## Request flow

1. Feature constructs URLRequest.
2. AuthenticatedHTTPClient verifies HTTPS and host allow-list.
3. AuthenticationSession loads credentials from CredentialStore.
4. If access token is current, it is returned. If expired, the session asks TokenRefreshing for replacement tokens and persists them.
5. AuthenticatedHTTPClient replaces Authorization with `Bearer <access-token>`.
6. Base HTTPClient sends the request.
7. On 2xx, data and response are returned.
8. On 401, AuthenticatedHTTPClient asks the session for a forced refresh and retries exactly once.
9. A second 401 or refresh failure is surfaced; retries do not loop.

## Credential handling

- Tokens live in Keychain only.
- UserDefaults remains for non-sensitive preferences.
- Keychain records are device-only and unavailable before first unlock after reboot.
- Credential values are not placed in environment variables, Info.plist, xcconfig, source files, analytics, or logs.
- Logout deletes the Keychain item.
- No OAuth client secret is embedded in the app. If a future provider requires a client secret that cannot safely be public, that exchange belongs on a trusted server.

## CI and repository security

- GitHub Actions permissions remain `contents: read` unless a job explicitly needs more.
- Every checkout uses `persist-credentials: false`.
- CI rejects tracked signing/key material and environment secret files.
- CI additionally scans tracked text for common private-key and credential-assignment patterns while avoiding token-value output.
- Third-party actions remain pinned to immutable commit SHAs.

## Testing

Unit tests cover:

- current tokens are returned without refresh;
- expired tokens refresh and persist replacement credentials;
- missing/expired credentials without refresh capability fail closed;
- sign-out clears credentials;
- authenticated requests replace stale Authorization headers;
- credentials are refused for HTTP and unapproved hosts;
- a 401 causes at most one refresh/retry;
- the retry uses the replacement access token.

The existing stable GitHub Actions matrix remains the authoritative build/test environment.

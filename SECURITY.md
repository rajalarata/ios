# Security policy

## Reporting

Do not publish credentials, signing certificates, provisioning profiles, API keys, access or refresh tokens, private user data, or exploitable security details in a public issue.

Use GitHub's private vulnerability reporting feature when it is enabled for this repository. If private reporting is unavailable, contact the repository owner through a private channel before disclosing details publicly.

## Repository rules

- Secrets, tokens, and signing material must stay outside Git history.
- GitHub Actions receives read-only repository contents unless a workflow explicitly requires more.
- Checkout credentials must not persist into later workflow steps unless a reviewed job explicitly requires authenticated Git operations.
- Third-party actions are pinned to immutable commit SHAs.
- External Swift dependencies require a documented justification and review before introduction.

## Application credentials

- Authentication tokens are stored only through `CredentialStore`; the live implementation uses the iOS Keychain.
- `UserDefaults`, `.xcconfig`, `Info.plist`, source files, logs, analytics, and crash annotations are not credential stores.
- Authenticated requests must use HTTPS and an explicit destination-host allow-list.
- An HTTP 401 may trigger at most one token refresh and one request retry.
- Sign-out removes locally stored authentication credentials.
- Confidential OAuth/client secrets must not be embedded in the iOS application. Any flow requiring a confidential secret belongs on trusted server infrastructure.

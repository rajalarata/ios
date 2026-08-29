# Security policy

## Reporting

Do not publish credentials, signing certificates, provisioning profiles, API keys, private user data, or exploitable security details in a public issue.

Use GitHub's private vulnerability reporting feature when it is enabled for this repository. If private reporting is unavailable, contact the repository owner through a private channel before disclosing details publicly.

## Repository rules

- Secrets and signing material must stay outside Git history.
- GitHub Actions receives read-only repository contents unless a workflow explicitly requires more.
- Third-party actions are pinned to immutable commit SHAs.
- External Swift dependencies require a documented justification and review before introduction.

#!/usr/bin/env bash
set -euo pipefail

result_bundle="${1:?xcresult path is required}"

report="$(xcrun xccov view --report --only-targets "$result_bundle")"

{
  echo "### Code coverage"
  echo
  echo '```text'
  printf '%s\n' "$report"
  echo '```'
} >> "${GITHUB_STEP_SUMMARY:?GITHUB_STEP_SUMMARY is required}"

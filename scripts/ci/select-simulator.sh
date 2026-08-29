#!/usr/bin/env bash
set -euo pipefail

runtime_version="${1:-latest}"
preferred_device="${2:-}"
json="$(xcrun simctl list devices available --json)"

if [[ "$runtime_version" == "latest" ]]; then
  runtime_identifier="$(python3 -c '
import json, re, sys
data = json.load(sys.stdin)
runtimes = [key for key in data["devices"] if "SimRuntime.iOS-" in key]
if not runtimes:
    raise SystemExit("No available iOS simulator runtime found")
def version(key):
    match = re.search(r"iOS-(\d+)-(\d+)", key)
    return tuple(map(int, match.groups())) if match else (0, 0)
print(max(runtimes, key=version))
' <<< "$json")"
else
  runtime_identifier="com.apple.CoreSimulator.SimRuntime.iOS-${runtime_version//./-}"
fi

select_existing() {
  local preferred="$1"
  python3 -c '
import json, sys
runtime = sys.argv[1]
preferred = sys.argv[2]
data = json.load(sys.stdin)
devices = data["devices"].get(runtime, [])
if preferred:
    exact = [device for device in devices if device.get("isAvailable") and device["name"] == preferred]
    if exact:
        print(exact[0]["udid"])
    raise SystemExit
iphones = [device for device in devices if device.get("isAvailable") and device["name"].startswith("iPhone")]
if iphones:
    print(iphones[0]["udid"])
' "$runtime_identifier" "$preferred" <<< "$json"
}

udid="$(select_existing "$preferred_device")"

if [[ -z "$udid" && -n "$preferred_device" ]]; then
  if xcrun simctl list devicetypes | grep -Fq "$preferred_device"; then
    udid="$(xcrun simctl create "CI ${preferred_device}" "$preferred_device" "$runtime_identifier")"
  else
    echo "Preferred simulator '${preferred_device}' is unavailable; falling back to another iPhone." >&2
    udid="$(select_existing "")"
  fi
fi

if [[ -z "$udid" ]]; then
  echo "No compatible iPhone simulator found for ${runtime_identifier}" >&2
  exit 1
fi

echo "platform=iOS Simulator,id=${udid}"

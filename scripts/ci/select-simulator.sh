#!/usr/bin/env bash
set -euo pipefail

runtime_version="${1:-latest}"
preferred_device="${2:-}"

json="$(xcrun simctl list devices available --json)"

if [[ "$runtime_version" == "latest" ]]; then
  runtime_identifier="$(printf '%s' "$json" | python3 -c '
import json, re, sys
data = json.load(sys.stdin)
runtimes = [key for key in data["devices"] if "SimRuntime.iOS-" in key]
if not runtimes:
    raise SystemExit("No available iOS simulator runtime found")
def version(key):
    match = re.search(r"iOS-(\d+)-(\d+)", key)
    return tuple(map(int, match.groups())) if match else (0, 0)
print(max(runtimes, key=version))
')"
else
  runtime_identifier="com.apple.CoreSimulator.SimRuntime.iOS-${runtime_version//./-}"
fi

udid="$(printf '%s' "$json" | python3 - "$runtime_identifier" "$preferred_device" <<'PY'
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
PY
)"

if [[ -z "$udid" && -n "$preferred_device" ]]; then
  device_type="com.apple.CoreSimulator.SimDeviceType.${preferred_device// /-}"
  device_type="${device_type//mini/mini}"
  if xcrun simctl list devicetypes | grep -Fq "$preferred_device"; then
    udid="$(xcrun simctl create "CI ${preferred_device}" "$preferred_device" "$runtime_identifier")"
  fi
fi

if [[ -z "$udid" ]]; then
  echo "No compatible iPhone simulator found for ${runtime_identifier}" >&2
  exit 1
fi

echo "platform=iOS Simulator,id=${udid}"

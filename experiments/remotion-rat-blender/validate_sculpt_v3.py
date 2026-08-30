import json
import sys

manifest_path = sys.argv[1]
with open(manifest_path, "r", encoding="utf-8") as f:
    data = json.load(f)

errors = []

if data.get("refinement_pass", 0) < 3:
    errors.append("refinement_pass must be >= 3")

quality = data.get("quality_gate", {})
for key in ("visual_sculpt_gate", "skin_weights_preserved", "neutral_qa_six_views"):
    if not quality.get(key):
        errors.append(f"{key} must be true")

metrics = data.get("sculpt_metrics", {})
for key in ("head_width", "head_depth", "muzzle_projection", "shoulder_width", "waist_width"):
    if key not in metrics:
        errors.append(f"missing sculpt metric {key}")

head_width = metrics.get("head_width")
head_depth = metrics.get("head_depth")
if head_width and head_depth:
    ratio = head_width / head_depth
    if not (0.78 <= ratio <= 1.12):
        errors.append(f"head width/depth ratio {ratio:.3f} outside target")

if metrics.get("muzzle_projection", 0) < 0.28:
    errors.append("muzzle_projection too small")

shoulder_width = metrics.get("shoulder_width")
waist_width = metrics.get("waist_width")
if shoulder_width and waist_width and shoulder_width <= waist_width * 1.08:
    errors.append("torso lacks shoulder-to-waist taper")

if errors:
    print("SCULPT V3 GATE: FAIL")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("SCULPT V3 GATE: PASS")

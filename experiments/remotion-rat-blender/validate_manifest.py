import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text())

assert data["bones"] >= 27, data
assert data["unweighted_vertices"] == 0, data
assert data["weighted_vertices"] >= 10000, data
assert data["max_weight_sum_error"] < 1e-4, data
assert 45000 <= data["scene_triangles"] <= 350000, data
assert len(data["skinned_meshes"]) >= 4, data
assert data["quality_gate"]["continuous_body_skin"] is True
assert data["quality_gate"]["separate_skinned_clothing"] is True
assert data["quality_gate"]["segmented_tail_rig"] is True
assert data["quality_gate"]["facial_control_bones"] is True
assert len(data["quality_gate"]["qa_turntable_views"]) == 5

print("manifest validation passed")
print(json.dumps(data, indent=2))

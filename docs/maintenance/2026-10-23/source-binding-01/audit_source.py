"""Static AST and byte bindings only; does not execute project source."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
bindings = []
for name in ("SOURCE_BINDINGS.json", "DEPENDENCY_BINDINGS.json"):
    bindings.extend(json.loads((ROOT / name).read_text(encoding="utf-8-sig")))
index = []
trees = {}
for binding in bindings:
    source = Path(binding["source"])
    snapshot = Path(binding["snapshot"])
    raw = snapshot.read_bytes()
    assert len(raw) <= 2 * 2**20
    expected = binding["sha256"].lower()
    assert hashlib.sha256(raw).hexdigest() == expected
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
    text = raw.decode("utf-8-sig")
    tree = ast.parse(text, filename=str(source))
    trees[source.name] = tree
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fields = []
            for child in ast.walk(node):
                if isinstance(child, ast.Subscript) and isinstance(child.slice, ast.Constant) and isinstance(child.slice.value, str):
                    fields.append({"expression": ast.unparse(child), "line": child.lineno, "context": type(child.ctx).__name__})
            functions.append({"name": node.name, "first_line": node.lineno, "last_line": node.end_lineno, "literal_subscripts": fields})
    index.append({"source": str(source), "sha256": expected, "functions": functions})

def function(filename, name):
    found = [n for n in ast.walk(trees[filename]) if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(found) == 1, (filename, name)
    return found[0]

checks = []
def check(name, condition):
    assert condition, name
    checks.append({"name": name, "passed": True})

for name in ("register", "register_multi"):
    node = function("rap_backend.py", name)
    fits = [n for n in ast.walk(node) if isinstance(n, ast.Call) and ast.unparse(n.func) == "fit_transformations"]
    check(name + "_fit_direction_cond_to_pred", len(fits) == 1 and [ast.unparse(a) for a in fits[0].args[:2]] == ["batch['pointclouds']", "pred"])
    check(name + "_public_placeholder", any(isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "pointclouds_gt" and ast.unparse(v) == "torch.from_numpy(cond).to(self.device)" for k, v in zip(n.keys, n.values)) for n in ast.walk(node)))

prepare = function("modeling.py", "_prepare_data")
check("prepare_requires_gt_named_key", any(isinstance(n, ast.Subscript) and ast.unparse(n) == "data_dict['pointclouds_gt']" for n in ast.walk(prepare)))
sample = function("modeling.py", "sample_rectified_flow")
prepared = [n for n in ast.walk(sample) if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and ast.unparse(n.value.func) == "self._prepare_data"]
check("sample_discards_prepare_first_return", len(prepared) == 1 and isinstance(prepared[0].targets[0], ast.Tuple) and ast.unparse(prepared[0].targets[0].elts[0]) == "_")
sampler_calls = [n for n in ast.walk(sample) if isinstance(n, ast.Call) and isinstance(n.func, ast.Call) and ast.unparse(n.func.func) == "get_sampler"]
check("sampler_x0_and_condition_are_cond", len(sampler_calls) == 1 and {k.arg: ast.unparse(k.value) for k in sampler_calls[0].keywords}.get("x_0") == "cond" and {k.arg: ast.unparse(k.value) for k in sampler_calls[0].keywords}.get("condition") == "cond")
test = function("modeling.py", "test_step")
check("default_test_calls_training_forward", any(isinstance(n, ast.Call) and ast.unparse(n.func) == "self.forward" for n in ast.walk(test)))
demo = function("demo.py", "main")
check("demo_calls_trainer_test", any(isinstance(n, ast.Call) and ast.unparse(n.func) == "trainer.test" for n in ast.walk(demo)))
flow = function("sampler.py", "flow_sampler")
check("raw_endpoint_stored_separately_from_rigid_step", any(isinstance(n, ast.Assign) and [ast.unparse(t) for t in n.targets] == ["trajectory[step]"] and ast.unparse(n.value) == "x_0_hat.detach().clone()" for n in ast.walk(flow)))
normal = function("rap_backend.py", "_normalize_parts")
check("normalization_has_no_file_reader", not any(isinstance(n, ast.Call) and ast.unparse(n.func) in ("open", "np.load", "np.loadtxt", "torch.load") for n in ast.walk(normal)))
check("twenty_files_bound", len(index) == 20)
size = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
check("dossier_under_8MiB", size < 8 * 2**20)
(ROOT / "AST_INDEX.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
(ROOT / "STATIC_CHECKS.json").write_text(json.dumps({"checks": checks, "passed": True, "source_files": len(index), "project_source_executed": False, "numerical_imports_requested": 0, "raw_or_reference_reads": 0}, indent=2), encoding="utf-8")
print(json.dumps({"passed": True, "checks": len(checks), "source_files": len(index), "project_source_executed": False}))

"""Derive canonical environment evidence, source imports, and reference requirements."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize(name):
    return re.sub(r"[-_.]+", "-", name.lower())


class Imports(ast.NodeVisitor):
    def __init__(self):
        self.functions = []
        self.rows = []

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        self.generic_visit(node)
        self.functions.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Import(self, node):
        for name in node.names:
            self.rows.append({"module": name.name, "line": node.lineno, "inside_function": ".".join(self.functions) or None})

    def visit_ImportFrom(self, node):
        self.rows.append({"module": "." * node.level + (node.module or ""), "names": [n.name for n in node.names],
                          "line": node.lineno, "inside_function": ".".join(self.functions) or None})


def main():
    raw = load(PHASE / "LINUX_OBSERVATION.json")
    supplement = load(PHASE / "LINUX_SUPPLEMENT.json")
    aliases = {r["path"]: r["resolved"] for r in supplement["path_aliases"]}

    def canonical(path):
        for old in sorted(aliases, key=len, reverse=True):
            if path == old or path.startswith(old + "/"):
                return aliases[old] + path[len(old):]
        return path

    environments = []
    for env in raw["environments"]:
        packages, records = {}, {}
        for item in env["packages"]:
            key = canonical(item["metadata_path"])
            if key in packages:
                assert packages[key]["version"] == item["version"]
            else:
                packages[key] = {**item, "canonical_metadata_path": key}
        for item in env["record_checks"]:
            key = canonical(item["path"])
            if key in records:
                assert records[key].get("sha256") == item.get("sha256")
            records[key] = item
        environments.append({"prefix": env["prefix"], "site_paths_raw": env["sites"],
                             "site_paths_canonical": sorted({canonical(p) for p in env["sites"]}),
                             "interpreter": env.get("interpreter"), "packages": list(packages.values()),
                             "raw_package_rows": len(env["packages"]), "unique_metadata_directories": len(packages),
                             "unique_python_record_checks": len(records), "record_states": dict(Counter(r["state"] for r in records.values())),
                             "conda_packages": env.get("conda_packages", [])})
    claim_counts = dict(Counter(r["a4_state"] for r in raw["claims"]))
    assert claim_counts == {"EXACT_MATCH": 72}
    save(PHASE / "ENVIRONMENT_SUMMARY.json", {"environments": environments, "path_aliases": supplement["path_aliases"],
                                              "linux_hash_claims": claim_counts, "claim_occurrences": 72,
                                              "unique_claim_paths": len({r["recorded_path"] for r in raw["claims"]}),
                                              "installed_python_RECORD_checks_are_not_upstream_provenance_authentication": True,
                                              "cpu_probe": {k: v for k, v in load(PHASE / "CPU_PROBE.json").items() if k not in {"torch_build_config", "components"}}})
    graph = []
    roots = {"rap-main": REPO, "rap-slam": REPO.parent / "RAP-SLAM"}
    groups = {"rap-main": ["rectified_point_flow", "dataset_process", "rap_runtime"], "rap-slam": ["rap_slam"]}
    for root, folders in groups.items():
        paths = [p for folder in folders for p in (roots[root] / folder).rglob("*.py")]
        if root == "rap-main":
            paths += [REPO / p for p in ("sample.py", "demo.py", "app.py", "scripts/run.py")]
        else:
            paths += [roots[root] / p for p in ("scripts/run_pipeline.py", "scripts/eval_external_trajectory.py", "scripts/eval_paper_metrics.py")]
        for path in sorted(set(paths)):
            content = path.read_bytes()
            parsed = ast.parse(content.decode("utf-8-sig"))
            imports = Imports()
            imports.visit(parsed)
            graph.append({"id": root + ":" + path.relative_to(roots[root]).as_posix(), "bytes": len(content),
                          "sha256": hashlib.sha256(content).hexdigest(), "imports": imports.rows})
    save(REPO / "docs/environment/DEPENDENCIES.json", {"scope": "STATIC_CURRENT_RUNTIME_SOURCE_IMPORTS_NOT_TRANSITIVE_INSTALL_LOCK",
                                                       "files": graph, "dynamic_import_completeness_claimed": False,
                                                       "env_evidence": "../maintenance/2026-11-04/environment-readiness-01/ENVIRONMENT_SUMMARY.json"})
    rap = environments[0]
    by_name = {normalize(p["name"]): p for p in rap["packages"]}
    requirements = REPO / "environment/requirements"
    requirements.mkdir(parents=True, exist_ok=True)
    lines = ["# Observed RAP environment metadata, 2026-11-04; not a clean-build or hash lock.",
             "# Use only with docs/environment/SETUP.md; no package source is authenticated by this file."]
    lines += [f"{p['name']}=={p['version']}" for p in sorted(rap["packages"], key=lambda r: normalize(r["name"]))]
    (requirements / "observed-rap.constraints.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    profiles = {
        "core": ["numpy", "scipy", "h5py", "lightning", "torchmetrics", "hydra-core", "omegaconf", "diffusers", "huggingface-hub", "rich", "matplotlib", "pandas", "pillow", "trimesh", "open3d", "natsort", "tqdm", "addict", "wandb"],
        "slam": ["kiss-icp", "gtsam", "evo"],
        "render-ui": ["mitsuba", "drjit", "gradio", "laspy"],
    }
    for name, names in profiles.items():
        lines = ["# Reference profile from the observed RAP environment; see SETUP.md first.", "-c observed-rap.constraints.txt"]
        for key in names:
            item = by_name[key]
            lines.append(item["name"] + "==" + item["version"])
        (requirements / (name + ".txt")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    save(PHASE / "GENERATED_INVENTORY.json", {"static_runtime_files": len(graph), "static_import_edges": sum(len(r["imports"]) for r in graph),
                                               "reference_distribution_pins": len(rap["packages"]),
                                               "environment_counts": [{"prefix": e["prefix"], "metadata_directories": e["unique_metadata_directories"],
                                                                       "record_checks": e["unique_python_record_checks"]} for e in environments],
                                               "profiles": profiles, "source_tree_commit_for_pytorch3d": None, "muon_installed": "muon" in by_name})
    print(json.dumps(load(PHASE / "GENERATED_INVENTORY.json"), ensure_ascii=False))


if __name__ == "__main__":
    main()

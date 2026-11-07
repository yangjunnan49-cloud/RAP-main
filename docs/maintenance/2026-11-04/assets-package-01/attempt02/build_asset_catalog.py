"""Classify frozen source identities and inspect only permitted dataset text metadata."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[3]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    baseline = load(PHASE / "BASELINE.json")
    records = rows(PHASE / "SOURCE_FILES.jsonl")
    roots = {key: Path(value) for key, value in baseline["source_roots"].items()}
    by_key = {(r["root"], r["path"]): r for r in records}
    previous = rows(REPO / "docs/experiments/catalog.jsonl")
    units = {}
    for row in previous:
        units[(row["root"], row["path"])] = {"id": row["id"], "root": row["root"], "path": row["path"], "kind": row["kind"],
                                                "execution_state_from_A2": row["execution_state"], "source_documentation": "A2_CATALOG_SNAPSHOT",
                                                "opaque_metadata_only": "portable_graph_20261031" in row["path"].lower()}

    def register(root, path, kind):
        units[(root, path)] = {"id": root + ":" + path, "root": root, "path": path, "kind": kind,
                              "execution_state_from_A2": None, "source_documentation": "A5_SOURCE_IDENTITY_CLASSIFICATION", "opaque_metadata_only": False}

    register("datasets", "data_odometry_velodyne", "observed_odometry_pointcloud_collection")
    register("datasets", "oxford_spires", "partial_reference_only_collection")
    register("datasets", "part2", "unrelated_or_unclassified_retained_EPUB")
    register("rap-main", "weights", "current_weight_and_cache_metadata_collection")
    for path in sorted({r["path"].split("/")[1] for r in records if r["root"] == "rap-main" and r["path"].startswith("demo_example_data/")}):
        register("rap-main", "demo_example_data/" + path, "local_upstream_demo_pointcloud_collection")
    for path in sorted({r["path"].split("/")[1] for r in records if r["root"] == "rap-slam" and r["path"].startswith("data/")}):
        register("rap-slam", "data/" + path, "downstream_data_or_derived_reference_collection")
    for phase in ("code-paths-01", "environment-readiness-01"):
        register("rap-main", "docs/maintenance/2026-11-04/" + phase, "migration_maintenance_after_A2_snapshot")
    for root in roots:
        register(root, "", "other_root_assets_preserved")
    membership, grouped = [], defaultdict(list)
    for row in records:
        relative = row["path"]
        candidate = relative
        while (row["root"], candidate) not in units:
            candidate = candidate.rpartition("/")[0]
        owner = units[(row["root"], candidate)]["id"]
        grouped[owner].append(row)
        membership.append({"asset": row["root"] + ":" + row["path"], "primary_bundle_id": owner, "sha256": row["sha256"],
                           "bytes": row["bytes"], "prior_category": row["prior_category"], "opaque_raw_copy_only": row["opaque_experiment"]})
    output_units = []
    for unit in sorted(units.values(), key=lambda r: r["id"]):
        members = grouped[unit["id"]]
        if not members:
            continue
        name = hashlib.sha256(unit["id"].encode()).hexdigest()[:20] + ".jsonl"
        member_path = PHASE / "bundles" / name
        member_path.parent.mkdir(exist_ok=True)
        value = "".join(json.dumps({"asset": r["root"] + ":" + r["path"], "sha256": r["sha256"], "bytes": r["bytes"]}, ensure_ascii=False) + "\n" for r in members)
        member_path.write_text(value, encoding="utf-8")
        output_units.append({**unit, "files": len(members), "logical_bytes": sum(r["bytes"] for r in members),
                             "member_manifest": member_path.relative_to(PHASE).as_posix(), "member_manifest_sha256": hashlib.sha256(value.encode()).hexdigest(),
                             "current_scientific_or_training_admission_granted": False, "package_volumes": None})
    (PHASE / "BUNDLES.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in output_units), encoding="utf-8")
    (PHASE / "ASSET_MEMBERSHIP.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in membership), encoding="utf-8")
    assert len(membership) == len({r["asset"] for r in membership}) == len(records)

    text_reads = []
    def text_info(root, path, columns=None):
        row = by_key.get((root, path))
        if row is None:
            return None
        assert not row["opaque_experiment"] and not "portable_graph_20261031" in path.lower()
        source = roots[root] / path
        raw = source.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["sha256"]
        lines = [line for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
        value = {"asset": root + ":" + path, "sha256": row["sha256"], "nonempty_lines": len(lines)}
        if columns is not None:
            value["all_nonempty_rows_have_expected_columns"] = all(len(line.split()) == columns for line in lines)
            value["expected_columns"] = columns
        text_reads.append({"asset": value["asset"], "sha256": row["sha256"], "purpose": "DATASET_FORMAT_AND_COUNT_ONLY"})
        return value

    datasets = []
    candidates = [("datasets", "data_odometry_velodyne/dataset", "KITTI_NAME_FROM_PATH_AND_EXISTING_LOADER_CONTRACT"),
                  ("rap-slam", "data/kitti/dataset", "DOWNSTREAM_KITTI_REFERENCE_COPY"),
                  ("rap-slam", "data/poss/dataset", "POSS_NAME_FROM_PATH_AND_EXISTING_PROTOCOL")]
    for root, prefix, label in candidates:
        seqs = sorted({r["path"][len(prefix) + 1:].split("/")[1] for r in records if r["root"] == root and r["path"].startswith(prefix + "/sequences/")})
        for sequence in seqs:
            start = prefix + "/sequences/" + sequence + "/"
            members = [r for r in records if r["root"] == root and r["path"].startswith(start)]
            bins = [r for r in members if re.fullmatch(re.escape(start) + r"velodyne/[0-9]+\.bin", r["path"])]
            frame_ids = sorted(int(Path(r["path"]).stem) for r in bins)
            intervals = []
            for frame in frame_ids:
                if not intervals or frame != intervals[-1][1] + 1:
                    intervals.append([frame, frame])
                else:
                    intervals[-1][1] = frame
            missing = sorted(set(range(frame_ids[0], frame_ids[-1] + 1)) - set(frame_ids)) if frame_ids else []
            pose = text_info(root, prefix + "/poses/" + sequence + ".txt", 12)
            times = text_info(root, start + "times.txt", 1)
            calibration = by_key.get((root, start + "calib.txt"))
            datasets.append({"id": root + ":" + prefix + ":" + sequence, "name_or_role_from_existing_path": label,
                             "source_url": None, "original_provider_release_or_download_authentication": "NOT_REESTABLISHED_IN_A5",
                             "sequence": sequence, "observed_cloud_files": len(bins), "cloud_bytes": sum(r["bytes"] for r in bins),
                             "first_frame_id": frame_ids[0] if frame_ids else None, "last_frame_id": frame_ids[-1] if frame_ids else None,
                             "observed_frame_intervals_inclusive": intervals,
                             "missing_ids_inside_observed_range_count": len(missing), "missing_ids_preview": missing[:100],
                             "all_bin_bytes_divisible_by_16": all(r["bytes"] % 16 == 0 for r in bins) if bins else None,
                             "zero_byte_cloud_files": sum(r["bytes"] == 0 for r in bins),
                             "observed_bin_byte_range": [min(r["bytes"] for r in bins), max(r["bytes"] for r in bins)] if bins else None,
                             "pose_text": pose, "timestamps_text": times, "calibration_asset": (root + ":" + calibration["path"]) if calibration else None,
                             "calibration_sha256": calibration["sha256"] if calibration else None,
                             "cloud_and_local_pose_count_equal": len(bins) == pose["nonempty_lines"] if pose and bins else None,
                             "cloud_and_local_timestamp_count_equal": len(bins) == times["nonempty_lines"] if times and bins else None,
                             "local_coverage_state": "OBSERVED_SUBSET_OR_COUNT_ONLY_NOT_PROVIDER_COMPLETENESS_CERTIFICATE",
                             "raw_vs_corrected_coordinate_or_physical_reference_newly_authenticated": False,
                             "training_validation_test_membership_admitted": False})
    spires = [r for r in records if r["root"] == "datasets" and r["path"].startswith("oxford_spires/")]
    save(PHASE / "DATASETS.json", {"odometry_format_collections": datasets,
                                   "oxford_spires": {"ordinary_files": len(spires), "gt_files": [r["path"] for r in spires if r["path"].startswith("oxford_spires/gt/")],
                                                     "pcd_files": sum(r["path"].lower().endswith(".pcd") for r in spires), "state": "GT_ONLY_PARTIAL_NO_SCAN_COMPLETENESS_CLAIM"},
                                   "raw_OXTS_source_authentication": "NOT_REESTABLISHED",
                                   "raw_OXTS_named_paths_observed": [r["root"] + ":" + r["path"] for r in records if r["root"] == "datasets" and "oxts" in r["path"].lower()],
                                   "datasets_part2": {"state": "UNRELATED_OR_UNCLASSIFIED_RETAINED_NOT_RESEARCH_DATA", "files": [r for r in records if r["root"] == "datasets" and r["path"].startswith("part2/")]},
                                   "no_cloud_array_or_calibration_transform_computation_performed": True})
    models = defaultdict(list)
    for row in records:
        if row["path"].lower().endswith((".ckpt", ".pth", ".pt", ".safetensors")):
            models[row["sha256"]].append(row)
    save(PHASE / "MODELS.json", {"unique_models_or_weight_artifacts": [{"sha256": digest, "bytes": members[0]["bytes"],
                                                                                     "physical_aliases": [r["root"] + ":" + r["path"] for r in members],
                                                                                     "source_url_or_original_release": None, "metadata_content_inspected_with_pickle_or_torch": False,
                                                                                     "training_resume_state_certified": False,
                                                                                     "architecture_identity_from_filename_only": True} for digest, members in sorted(models.items())],
                               "current_runtime_weight_filenames": [r["path"] for r in records if r["root"] == "rap-main" and r["path"].startswith("weights/") and r["path"].endswith((".ckpt", ".pth"))],
                               "RAPBackend_default_checkpoint_remains_rap_model_12": True})
    save(PHASE / "DATA_TEXT_READS.json", {"reads": text_reads, "PGC1_partial_results_semantically_read": False, "model_or_numpy_data_loads": 0})
    summary = {"source_files_owned": len(membership), "logical_bundles": len(output_units), "unique_current_and_historical_weight_digests": len(models),
               "zero_byte_ordinary_files_retained": sum(r["bytes"] == 0 for r in records),
               "local_odometry_sequence_records": len(datasets), "dataset_text_metadata_reads": len(text_reads),
               "bundle_kinds": dict(Counter(r["kind"] for r in output_units)), "unowned_files": 0,
               "partial_PGC1_outputs_semantically_read": False, "array_model_or_training_execution": False}
    save(PHASE / "CATALOG_SUMMARY.json", summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

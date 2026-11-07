"""Repair only GTSAM 4.2's redundant WHEEL tag field; preserve all runtime bytes."""
import argparse
import base64
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile
from packaging.utils import parse_wheel_filename


def sha(data):
    return hashlib.sha256(data).hexdigest()


def repair(wheel, expected_sha, destination, receipt):
    assert sha(wheel.read_bytes()) == expected_sha
    name, version, build, tags = parse_wheel_filename(wheel.name)
    assert name == "gtsam" and str(version) == "4.2" and len(tags) == 1
    tag = next(iter(tags))
    correct = str(tag)
    wrong = f"{tag.interpreter}-{tag.abi}-none-{tag.platform}"
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / wheel.name
    with zipfile.ZipFile(wheel) as source:
        infos = source.infolist()
        assert len({info.filename for info in infos}) == len(infos)
        original = {info.filename: source.read(info.filename) for info in infos}
    metadata, record = "gtsam-4.2.dist-info/WHEEL", "gtsam-4.2.dist-info/RECORD"
    assert not any(name.endswith(("RECORD.jws", "RECORD.p7s")) for name in original)
    lines = original[metadata].decode("utf-8").splitlines(keepends=True)
    assert [line.strip() for line in lines if line.startswith("Tag:")] == ["Tag: " + wrong]
    changed = dict(original)
    changed[metadata] = "".join("Tag: " + correct + "\n" if line.startswith("Tag:") else line for line in lines).encode("utf-8")
    table = io.StringIO(newline="")
    writer = csv.writer(table, lineterminator="\n")
    for info in infos:
        if info.is_dir() or info.filename == record:
            continue
        data = changed[info.filename]
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode("ascii")
        writer.writerow([info.filename, "sha256=" + digest, str(len(data))])
    writer.writerow([record, "", ""])
    changed[record] = table.getvalue().encode("utf-8")
    with zipfile.ZipFile(output, "x") as target:
        for info in infos:
            target.writestr(copy.copy(info), changed[info.filename], compress_type=info.compress_type)
    with zipfile.ZipFile(output) as target:
        assert set(target.namelist()) == set(original)
        differences = [path for path in original if target.read(path) != original[path]]
        assert set(differences) == {metadata, record}
        unchanged = [dict(path=path, bytes=len(original[path]), sha256=sha(original[path]))
                     for path in original if path not in differences]
        assert all(target.read(row["path"]) == original[row["path"]] for row in unchanged)
    value = dict(passed=True, original_wheel=str(wheel), original_sha256=expected_sha,
        derived_wheel=str(output), derived_sha256=sha(output.read_bytes()),
        old_tag=wrong, corrected_tag_from_published_filename=correct,
        changed_members=differences, all_other_member_bytes_unchanged=True,
        unchanged_members=unchanged, package_version_unchanged="4.2", numerical_source_or_binary_modified=False,
        specification="https://packaging.python.org/en/latest/specifications/binary-distribution-format/")
    receipt.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value[key] for key in ("passed", "derived_sha256", "old_tag", "corrected_tag_from_published_filename", "changed_members")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    repair(args.wheel, args.expected_sha256, args.destination, args.receipt)

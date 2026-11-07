"""Read WSL control-plane state without starting a Linux distribution."""
import argparse
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import winreg

PHASE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--label", required=True)
    args = p.parse_args()
    result = {"observed_utc": datetime.now(timezone.utc).isoformat(), "label": args.label,
              "linux_distribution_start_requested": False, "commands": [], "distributions_registry": []}
    for argv in (["wsl.exe", "--list", "--verbose"], ["wsl.exe", "--list", "--running", "--quiet"]):
        try:
            proc = subprocess.run(argv, capture_output=True, timeout=25)
            item = {"argv": argv, "exit_code": proc.returncode}
            for key, raw in (("stdout", proc.stdout), ("stderr", proc.stderr)):
                encoding = "utf-16-le" if b"\x00" in raw or raw.startswith(b"\xff\xfe") else "utf-8"
                item[key] = raw.decode(encoding, errors="replace").lstrip("\ufeff")
                item[key + "_base64"] = base64.b64encode(raw).decode("ascii")
            result["commands"].append(item)
        except (OSError, subprocess.TimeoutExpired) as exc:
            result["commands"].append({"argv": argv, "error": repr(exc)})
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Lxss") as root:
            for i in range(winreg.QueryInfoKey(root)[0]):
                name = winreg.EnumKey(root, i)
                with winreg.OpenKey(root, name) as distro:
                    row = {"registry_id": name}
                    for field in ("DistributionName", "BasePath", "Version", "DefaultUid"):
                        try:
                            row[field] = winreg.QueryValueEx(distro, field)[0]
                        except OSError:
                            row[field] = None
                    result["distributions_registry"].append(row)
    except OSError as exc:
        result["registry_error"] = repr(exc)
    target = PHASE / ("HOST_" + args.label + ".json")
    assert not target.exists(), "Refusing to replace prior observation"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    display = {**result, "commands": [{k: v for k, v in item.items() if not k.endswith("_base64")} for item in result["commands"]]}
    print(json.dumps(display, ensure_ascii=False))


if __name__ == "__main__":
    main()

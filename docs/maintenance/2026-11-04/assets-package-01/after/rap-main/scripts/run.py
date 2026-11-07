#!/usr/bin/env python3
"""Portable RAP launcher. Defaults to a JSON command plan without execution."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rap_runtime.launch import main

if __name__ == "__main__":
    raise SystemExit(main())

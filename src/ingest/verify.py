"""Verify raw archives against data/checksums.sha256.

Usage:  python -m src.ingest.verify
"""

from __future__ import annotations

import sys
from pathlib import Path

from .download import ROOT, MANIFEST, sha256


def main() -> int:
    entries = [
        ln.split(maxsplit=1)
        for ln in MANIFEST.read_text().splitlines()
        if ln.strip() and not ln.startswith("#")
    ]
    if not entries:
        print("No checksums recorded yet — run `make data` first.")
        return 1

    bad = 0
    for digest, rel in entries:
        path = ROOT / rel.strip()
        if not path.exists():
            print(f"MISSING  {rel.strip()}")
            bad += 1
        elif sha256(path) != digest:
            print(f"MISMATCH {rel.strip()}")
            bad += 1
        else:
            print(f"ok       {rel.strip()}")

    print(f"\n{len(entries) - bad}/{len(entries)} archives verified.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

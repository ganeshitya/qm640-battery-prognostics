"""Fetch source archives listed in :mod:`src.ingest.sources`.

Archives that the custodian serves directly are downloaded and hashed.
Archives behind an interstitial page are reported with their landing page and
expected destination, so the manual step is unambiguous and auditable.

Usage:  python -m src.ingest.download
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

from .sources import SOURCES, TOTAL_CELLS

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "checksums.sha256"


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def fetch(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    target = dest / url.rsplit("/", 1)[-1]
    if target.exists():
        print(f"      already present: {target.relative_to(ROOT)}")
        return target
    print(f"      downloading {url}")
    urllib.request.urlretrieve(url, target)
    return target


def main() -> int:
    print(f"QM640 corpus: {len(SOURCES)} sources, {TOTAL_CELLS} cells expected\n")
    digests: list[tuple[str, str]] = []
    manual: list = []

    for src in SOURCES:
        print(f"[{src.key}] {src.name} — {src.cells} cells, {src.chemistry}")
        dest = ROOT / src.dest
        if src.auto:
            for url in src.urls:
                try:
                    path = fetch(url, dest)
                    digests.append((sha256(path), str(path.relative_to(ROOT))))
                    print("      ok")
                except Exception as exc:                      # noqa: BLE001
                    print(f"      FAILED: {exc}")
                    manual.append(src)
        else:
            manual.append(src)
            print("      manual download required")
        print()

    if digests:
        existing = [
            ln for ln in MANIFEST.read_text().splitlines()
            if ln.startswith("#") or not ln.strip()
        ]
        MANIFEST.write_text("\n".join(existing + [f"{d}  {p}" for d, p in digests]) + "\n")
        print(f"Wrote {len(digests)} checksum(s) to {MANIFEST.relative_to(ROOT)}\n")

    if manual:
        print("=" * 72)
        print("MANUAL STEPS REQUIRED")
        print("=" * 72)
        for src in manual:
            print(f"\n  {src.name}  ({src.cells} cells)")
            print(f"    download from : {src.landing_page}")
            print(f"    save into     : {src.dest}/")
            if src.note:
                print(f"    note          : {src.note}")
        print("\nThen re-run `make data` to hash the downloaded files.")
        return 1

    print("All sources present and hashed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

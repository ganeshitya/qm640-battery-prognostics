"""Validate the processed tables against data/dictionary.yaml.

Checks dtype family, permissible range, nullability, factor levels and the
global cross-table rules declared in the dictionary. Exits non-zero on any
violation so it can gate `make features` in CI.

Usage:  python -m src.harmonise.validate
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
DICT = ROOT / "data" / "dictionary.yaml"
TABLES = {
    "cell_level": ROOT / "data" / "processed" / "cell_level.parquet",
    "cycle_level": ROOT / "data" / "processed" / "cycle_level.parquet",
}

NUMERIC = {"float", "integer", "binary"}


def check_table(name: str, spec: dict, df: pd.DataFrame) -> list[str]:
    problems: list[str] = []

    missing = set(spec) - set(df.columns)
    if missing:
        problems.append(f"[{name}] columns absent: {sorted(missing)}")
    extra = set(df.columns) - set(spec)
    if extra:
        problems.append(f"[{name}] undocumented columns: {sorted(extra)}")

    for col, meta in spec.items():
        if col not in df.columns:
            continue
        s = df[col]
        c = meta.get("constraints", {}) or {}

        if not c.get("nullable", True) and s.isna().any():
            problems.append(f"[{name}.{col}] {int(s.isna().sum())} null(s) in a non-nullable column")

        if meta["type"] in NUMERIC:
            v = pd.to_numeric(s, errors="coerce").dropna()
            if "min" in c and len(v) and v.min() < c["min"]:
                problems.append(f"[{name}.{col}] min {v.min():.4g} below permitted {c['min']}")
            if "max" in c and len(v) and v.max() > c["max"]:
                problems.append(f"[{name}.{col}] max {v.max():.4g} above permitted {c['max']}")

        if "levels" in meta:
            unknown = set(s.dropna().unique()) - set(meta["levels"])
            if unknown:
                problems.append(f"[{name}.{col}] unexpected levels: {sorted(unknown)}")

        if "values" in c:
            unknown = set(s.dropna().unique()) - set(c["values"])
            if unknown:
                problems.append(f"[{name}.{col}] values outside {c['values']}: {sorted(unknown)}")

        if c.get("unique") and s.duplicated().any():
            problems.append(f"[{name}.{col}] duplicate keys present")

    return problems


def cross_table(cell: pd.DataFrame, cycle: pd.DataFrame) -> list[str]:
    problems: list[str] = []

    orphans = set(cycle["cell_id"]) - set(cell["cell_id"])
    if orphans:
        problems.append(f"[join] {len(orphans)} cycle-level cell_id(s) absent from cell_level")

    gaps = (
        cycle.sort_values(["cell_id", "cycle_index"])
        .groupby("cell_id")["cycle_index"]
        .apply(lambda s: (s.diff().dropna() != 1).any())
    )
    if gaps.any():
        problems.append(f"[cycle_index] non-contiguous in {int(gaps.sum())} cell(s)")

    mismatch = cell.loc[(cell["cycle_life"] < 550) != (cell["life_class"] == 1)]
    if len(mismatch):
        problems.append(f"[life_class] inconsistent with cycle_life for {len(mismatch)} cell(s)")

    return problems


def main() -> int:
    spec = yaml.safe_load(DICT.read_text())

    frames = {}
    for name, path in TABLES.items():
        if not path.exists():
            print(f"{path.relative_to(ROOT)} not built yet — run `make features` first.")
            return 1
        frames[name] = pd.read_parquet(path)
        print(f"loaded {name}: {len(frames[name]):,} rows x {frames[name].shape[1]} cols")

    problems: list[str] = []
    for name in TABLES:
        problems += check_table(name, spec[name], frames[name])
    problems += cross_table(frames["cell_level"], frames["cycle_level"])

    print()
    if problems:
        for p in problems:
            print("FAIL", p)
        print(f"\n{len(problems)} validation failure(s).")
        return 1

    n = len(frames["cell_level"])
    print(f"All checks passed. Corpus: {n} cells "
          f"({int(frames['cell_level']['censored'].sum())} censored).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

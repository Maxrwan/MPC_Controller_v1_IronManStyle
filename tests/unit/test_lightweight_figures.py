"""Reproduce the three study figures solely from committed compact tables."""

import hashlib
import shutil
from pathlib import Path

from task007dp.figures import FIGURES, render


def test_three_figure_inventory_and_same_environment_reproduction(tmp_path):
    source = Path(__file__).resolve().parents[2] / "docs/task007d/p"
    tables = ["figure1_data.csv", "release_errors.csv", "benchmark_summary.csv", "accuracy.csv"]
    a, b = tmp_path / "first", tmp_path / "repeat"
    for folder in (a, b):
        folder.mkdir()
        for name in tables:
            shutil.copyfile(source / name, folder / name)
        assert render(folder) == FIGURES
        assert sorted(p.name for p in folder.glob("*.png")) == sorted(FIGURES)
    for name in FIGURES:
        assert (a / name).stat().st_size > 10_000
        assert (
            hashlib.sha256((a / name).read_bytes()).digest()
            == hashlib.sha256((b / name).read_bytes()).digest()
        )

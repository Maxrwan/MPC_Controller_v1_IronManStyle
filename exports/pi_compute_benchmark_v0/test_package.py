"""Focused packaging/evidence tests; no invented dynamics or timing thresholds."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmark import completed_plans, summarize, supervise
from common import ROOT, THREAD_ENV, clean, distribution, verify_sources


class EvidenceTests(unittest.TestCase):
    def test_frozen_source_hashes(self):
        self.assertEqual(
            verify_sources()["scientific_revision"], "48adbdf64d492592d15e23c917aca71fa58aa8a5"
        )

    def test_modified_source_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "results") as folder:
            folder = Path(folder)
            (folder / "source_manifest.json").write_text(
                json.dumps({"files": {"bad.py": {"sha256": "0" * 64, "bytes": 3}}})
            )
            (folder / "bad.py").write_text("bad")
            with patch("common.ROOT", folder), self.assertRaisesRegex(ValueError, "mismatch"):
                verify_sources()

    def test_empirical_percentiles_and_strict_exceedance(self):
        row = distribution([0.0, 0.1, 0.2], 0.1)
        self.assertEqual(row["count"], 3)
        self.assertAlmostEqual(row["median_s"], 0.1)
        self.assertAlmostEqual(row["p95_s"], 0.19)
        self.assertAlmostEqual(row["p99_s"], 0.198)
        self.assertEqual(row["exceeding_period_count"], 1)
        self.assertEqual(distribution([], 0.1)["mean_s"], None)

    def test_failed_solver_remains_in_population(self):
        rows = [
            {
                "startup": True,
                "warm_start": False,
                "success": False,
                "solver": {"solve_time": 0.3},
                "prepare_wall_s": 0.4,
            },
            {
                "startup": False,
                "warm_start": True,
                "success": True,
                "solver": {"solve_time": 0.01},
                "prepare_wall_s": 0.02,
            },
            {"startup": False, "success": False, "solver": None, "prepare_wall_s": 0.01},
        ]
        report = summarize(
            rows,
            [{"update_wall_s": 0.02}],
            [
                {"mode": "trajectory", "total_time": 0.015, "command_validation_time": 0.014},
                {"mode": "fallback", "total_time": 0.1, "command_validation_time": 0.09},
            ],
        )
        self.assertEqual(report["ipopt_all"]["count"], 2)
        self.assertEqual(report["preparation_all"]["count"], 3)
        self.assertEqual(report["ipopt_startup"]["maximum_s"], 0.3)
        self.assertEqual(report["ipopt_warm"]["count"], 1)
        self.assertEqual(report["tracker_update"]["exceeding_period_proportion"], 1.0)
        self.assertEqual(report["tracker_validated_applied"]["count"], 1)
        self.assertEqual(report["tracker_validated_applied"]["maximum_s"], 0.015)
        self.assertEqual(report["command_validation_applied"]["maximum_s"], 0.014)

    def test_nonfinite_is_explicit_json(self):
        self.assertEqual(clean(float("inf")), {"nonfinite": "inf"})
        json.dumps(clean({"raw": float("nan")}), allow_nan=False)

    def test_scenarios_are_distinct_and_bounded(self):
        data = json.loads((ROOT / "scenarios.json").read_text())
        self.assertEqual(data["duration_s"], 2.0)
        self.assertEqual(
            {w["name"] for w in data["windows"]},
            {"straight", "high_curvature", "curvature_transition"},
        )
        self.assertEqual(len({w["s_track_m"] for w in data["windows"]}), 3)
        self.assertTrue(all(len(w["initial_state"]) == 6 for w in data["windows"]))

    def test_partial_journal_recovers_only_completed_calls(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "results") as folder:
            folder = Path(folder)
            (folder / "progress.jsonl").write_text(
                '{"event":"prepare_begin","plan_id":0}\n'
                '{"event":"prepare_end","plan_id":0,"success":false}\n'
                '{"event":"prepare_begin","plan_id":1}\n{"event":'
            )
            self.assertEqual(completed_plans(folder), [{"plan_id": 0, "success": False}])

    def test_supervisor_timeout_is_explicit_and_retains_logs(self):
        real_popen = __import__("subprocess").Popen

        def controlled_child(command, **kwargs):
            return real_popen([sys.executable, "-c", "import time; time.sleep(10)"], **kwargs)

        with tempfile.TemporaryDirectory(dir=ROOT / "results") as folder:
            with patch("benchmark.subprocess.Popen", side_effect=controlled_child):
                observed = supervise(Path(folder), "straight", 0.05, False)
            self.assertTrue(observed["timed_out"])
            self.assertNotEqual(observed["exit_code"], 0)
            self.assertTrue((Path(folder) / "worker.log").exists())

    @unittest.skipUnless(sys.platform == "linux", "Numerical admission targets the Linux container")
    def test_controlled_failed_solver_is_retained_as_failed_window(self):
        os.environ.update(THREAD_ENV)
        sys.path.insert(0, str(ROOT / "vendor/src"))
        from runtime import compose
        from worker import run

        from apex.optimization.base import SolverResult

        class FailedSolver:
            def solve(self, request):
                return SolverResult(
                    False,
                    "CONTROLLED_TEST_FAILURE",
                    statistics={"solve_time": 0.123, "iterations": 9, "primal_infeasibility": 0.2},
                )

        def composition(tracker_class):
            components = compose(tracker_class)
            components[0].solver = FailedSolver()
            return components

        scenario = json.loads((ROOT / "scenarios.json").read_text())["windows"][0]
        with tempfile.TemporaryDirectory(dir=ROOT / "results") as folder:
            folder = Path(folder)
            with patch("runtime.compose", side_effect=composition):
                self.assertEqual(run(folder, scenario), 2)
            report = json.loads((folder / "worker_summary.json").read_text())
            self.assertEqual(report["status"], "FAILED_OR_INCOMPLETE")
            self.assertEqual(report["stop_reason"], "startup_failed")
            rows = json.loads((folder / "plans.json").read_text())
            self.assertEqual(rows[0]["solver"]["iterations"], 9)
            self.assertFalse(rows[0]["success"])
            self.assertFalse(rows[0]["packet_prepared"])


if __name__ == "__main__":
    unittest.main()

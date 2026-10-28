"""One shared pair of real nominal software smokes; never a qualification campaign."""

import pytest

from tools.apex_workbench import jobs
from tools.apex_workbench.lab_configuration import request_for
from tools.apex_workbench.tests.test_corrections import finished


@pytest.fixture(scope="session")
def lab_runs(tmp_path_factory):
    root = tmp_path_factory.mktemp("real-lab-workers")
    runs = []
    for case in ("VDL1_BASE", "VDL1_STEER_HIGH"):
        directory = jobs.start_run(
            "dynamic_lab",
            request_for(case),
            "Software smoke only; no scientific qualification",
            runs=root,
        )
        status = finished(directory)
        assert status["state"] == "completed", (status, (directory / "stderr.log").read_text())
        runs.append(directory)
    return runs

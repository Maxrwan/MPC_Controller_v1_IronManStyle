import importlib
import pkgutil

import apex
from apex.simulation.base import StepResult
from apex.state import state_vector


def test_all_subpackages_import():
    modules = list(pkgutil.walk_packages(apex.__path__, prefix="apex."))
    assert modules
    for module in modules:
        importlib.import_module(module.name)


def test_step_result_has_independent_info_and_no_invented_reward():
    first = StepResult(state_vector([0] * 6))
    second = StepResult(state_vector([0] * 6))
    first.info["event"] = "lap"
    assert second.info == {}
    assert first.reward is None
    assert not first.terminated
    assert not first.truncated

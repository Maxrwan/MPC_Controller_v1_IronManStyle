"""84 approved matrix designs; assertions remain unexecuted."""

import pytest
from oracle_support import assert_projection, cases, run_case

MATRIX_CASES = [c for c in cases() if c["case_id"].startswith("T")]


@pytest.mark.parametrize("case", MATRIX_CASES, ids=[c["case_id"] for c in MATRIX_CASES])
def test_reviewed_source_edge_projection(case):
    initial, result = run_case(case)
    assert_projection(case, initial, result)
    assert not {t.transition_id for t in result.transitions} & {
        "T04",
        "T05",
        "T07",
        "T08",
        "T10",
        "T12",
    }

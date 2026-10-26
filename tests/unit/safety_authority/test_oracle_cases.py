"""O4B focused literal cases: separate independent approval BEFORE selection.

NOT EXECUTED. Collection itself is unauthorized at this delivery stage. A later
execution assignment must authenticate/supply the external review document and
its digest described in oracle_support. No local approval, fixture status edit,
skip, xfail, or partial-prefix success substitutes for independent acceptance.
"""

import pytest
from oracle_support import (
    approved_selection,
    compare_core,
    independent_review,
    population,
    run_case,
    run_materialization,
)

# Fails collection closed when review is absent; no reducer import/call first.
# Excluded/incomplete cases create NO test instances and are NOT passes.
SELECTED_CASE_IDS = approved_selection()


def test_independent_full_trace_materialization_entry_gate(record_property):
    approval = independent_review()
    assert tuple(approval["accepted_case_ids"]) == SELECTED_CASE_IDS
    record_property("independent_review_record", approval["review_record_ref"])
    record_property("selected_literal_case_ids", approval["accepted_case_ids"])
    record_property("excluded_NOT_RUN_NOT_PASS", approval["excluded_cases"])


@pytest.mark.parametrize("case_id", SELECTED_CASE_IDS, ids=SELECTED_CASE_IDS)
def test_reviewed_literal_reduction(case_id, record_property):
    kind, case, _ = population()[case_id]
    record_property("case_id", case_id)
    if kind == "core":
        initial, result = run_case(case)
        report = compare_core(case, initial, result)
    else:
        report = run_materialization(case_id)
    record_property("materialization_version", report.materialization_version)
    record_property("original_row_bindings", report.original_row_bindings)
    report.assert_matches()

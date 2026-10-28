# V0.2-C review 1 reproduction

Exact reviewed candidate: `a6917a00c2ac48e69d3a28ca4e7c9fbf6d964052`. Run commands from `/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle`. The supplied scripts refuse or reuse only their designated disposable paths; preserve the original review outputs and use a fresh review root for any later repetition.

`run_reader_tests.py` is the initial failed harness and is retained as negative reviewer evidence. `run_reader_tests_fixed.py` accepts pytest fixture kwargs and uses separate output paths. Both substitute copies of existing WORK records for `lab_runs`; neither executes a worker. The fixed run selected 99 tests, deliberately excluding the half-grid software worker smoke and Streamlit view test.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:scripts:src \
  tools/apex_workbench/.venv/bin/python \
  /private/tmp/apex-v02c-independent-review-1/run_reader_tests_fixed.py \
  > /private/tmp/apex-v02c-independent-review-1/reader-tests-fixed.log 2>&1
```

Retained result: `reader-tests-fixed.log`, `pytest_exit_fixed.json`, exit 0, 99 passed/2 deselected. Initial failed harness: `reader-tests.log`, `pytest_exit.json`, exit 1, 25 passes/74 setup errors due exclusively to fixture replacement signature.

The identity probe binds a byte-identical copied retained record to show that path copies preserve run/worker/manifest identity. It then uses a mocked loader to assemble admission-only protocol fixtures, exercises actual `require_protocol_run` and `scientific_identity`, and raises a sentinel at `calculate`. It creates no qualification document, real or fixture-backed, and launches no model.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:scripts:src \
  tools/apex_workbench/.venv/bin/python \
  /private/tmp/apex-v02c-independent-review-1/probe_execution_identity.py \
  > /private/tmp/apex-v02c-independent-review-1/execution-identity.log 2>&1
```

Retained exact output: `execution-identity-results.json`: 17 distinct fixture paths, 16 distinct run IDs, duplicate execution admitted through the calculation sentinel; no calculation completed, no qualification document created, zero new model trajectories. The copy probe does not relabel the genuine interactive software record as real qualification input.

The scripts use the existing Workbench Python environment. No numerical native workload runs; tests use scalar angle arithmetic and byte/JSON/CSV readers. Do not treat these reproduction instructions as campaign or formal Verification authorization. Later correction reviews must name and inspect a new exact SHA.

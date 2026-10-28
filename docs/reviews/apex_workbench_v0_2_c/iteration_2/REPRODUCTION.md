# V0.2-C review 2 reproduction

Reviewed exact source: `4897686e79c13757d5ef5b4373b44d4cab99b5bf`. Working tree was clean. All reviewer writes are in `/private/tmp/apex-v02c-independent-review-2/`. Prior failed review/evidence remains unchanged.

`run_reader_tests.py` selects the 40 qualification tests. It replaces `lab_runs` with copies of the retained corrected-WORK BASE/STEER software smokes from `results/apex_workbench_v02c_work_20261029/review-q1-fix/real-lab-workers0/`. The two source-run directories are verified by the normal readers; no worker or model is executed. The copied records remain software evidence, without scientific qualification authority.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:scripts:src \
  tools/apex_workbench/.venv/bin/python \
  /private/tmp/apex-v02c-independent-review-2/run_reader_tests.py \
  > /private/tmp/apex-v02c-independent-review-2/reader-tests.log 2>&1
```

Retained result: `reader-tests.log`, `pytest_exit_fixed.json`, **40 passed**, exit 0, 0.38 s. The inherited exit-file name reflects the copied corrected review harness; there was no failed iteration-2 invocation.

`probe_execution_identity.py` independently constructs literal admission-only metadata, uses mocked bound-source/scientific-identity loading and the actual production protocol/identity gate, then raises a calculation sentinel. Duplicate run, worker and manifest identities are separately rejected. Unique identities and legitimate PID reuse with a different birth time reach the sentinel. No calculation completes and no qualification record is created.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:scripts:src \
  tools/apex_workbench/.venv/bin/python \
  /private/tmp/apex-v02c-independent-review-2/probe_execution_identity.py \
  > /private/tmp/apex-v02c-independent-review-2/execution-identity.log 2>&1
```

Exact result: `execution-identity-results.json`. These fixtures never become source-run manifests or real qualification output. The test suite's exact-directory-copy case separately exercises real verified copied bytes.

The scripts preserve previous outputs; a later repetition should use a fresh review path. No review command authorizes the real qualification campaign, full Verification, new physical assumptions, controller experiments or hardware work. The first report and reproduction document were byte-compared with their preserved repository copies using `cmp`; both match. Candidate status and revision were rechecked after the focused run.

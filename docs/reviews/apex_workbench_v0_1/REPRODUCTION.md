# Review evidence and reproduction

Target: `a0b4a98b14f53469735ca4dd9f7a93a7b0651860`. Evidence below is from this Mac,
not a portability claim. Never rerun into the retained evidence directory: use a fresh one
for another attempt. No product source changes were needed to reproduce the findings.

## Isolation used

The original checkout was clean at launcher descendant `a8e96ee95b99088bafb8ef2cb7a4d13f76c7905f`.
These setup commands created a detached local clone (read-only shared Git objects, independent
checkout/index) and reused the existing installed Workbench environment without installing packages:

```sh
git clone --shared --no-checkout --local \
  /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle \
  /private/tmp/apex-workbench-review-a0b4a98-20261027
git -C /private/tmp/apex-workbench-review-a0b4a98-20261027 checkout --detach \
  a0b4a98b14f53469735ca4dd9f7a93a7b0651860
ln -s /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/tools/apex_workbench/.venv \
  /private/tmp/apex-workbench-review-a0b4a98-20261027/tools/apex_workbench/.venv
```

All eight delivery-manifest hashes matched. The test header records ROOT and apex.__file__
inside this clone. The harness asserts that source location and is intentionally specific
to this review setup. Retained local evidence:
`/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/apex_workbench_review_20261027/`.
The clone remains available for inspection. Its only untracked entry is the tooling .venv
symlink (the directory-only ignore pattern does not hide that symlink); tracked contents are
unchanged. No running test processes remain.

## Exact focused test invocation

Working directory: `/private/tmp/apex-workbench-review-a0b4a98-20261027`.

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=.:scripts:src \
tools/apex_workbench/.venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import importlib.metadata, json, sys, apex, pytest; from tools.apex_workbench.configuration import ROOT; print(json.dumps({"review_root":str(ROOT),"apex_module":apex.__file__,"python":sys.version,"packages":{n:importlib.metadata.version(n) for n in ["numpy","scipy","pandas","matplotlib","streamlit","plotly","psutil","threadpoolctl","pytest"]}})); raise SystemExit(pytest.main(sys.argv[1:]))' \
-q tools/apex_workbench/tests tests/unit/test_frenet.py tests/unit/test_baseline.py \
  tests/unit/test_runner.py --durations=5 \
  --basetemp=/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/apex_workbench_review_20261027/pytest \
> /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/apex_workbench_review_20261027/focused-tests.log 2>&1
```

Exit 0; **85 passed**, including both original-entry-point parity tests. No complete scientific
regression or benchmark suite was run. The original 127-pass WORK evidence was inspected as
historical context, not counted as newly executed review tests.

## Exact probe template and modes

Each mode ran sequentially in a fresh Python process from the same pinned working directory.
The original harness path below is an ignored evidence file. The committed
[`review_probes.py`](review_probes.py) is an AST-identical, formatted review-only copy for inspection/reproduction. The executed
raw harness remains unchanged in local evidence; hashes for both copies are recorded.
Replace the evidence argument with a fresh directory for any new run; the comparison mode needs
the focused pytest LQR output in that directory first.

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=.:scripts:src \
tools/apex_workbench/.venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import runpy, sys; sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name="__main__")' \
/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/apex_workbench_review_20261027/review_probes.py \
<MODE> \
/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/apex_workbench_review_20261027 \
> /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/apex_workbench_review_20261027/probe-<MODE>.log 2>&1
```

| MODE | Technique and bounds | Observation |
|---|---|---|
| `orphan` | One real dynamic worker; SIGKILL only its supervisor; second Popen intercepted; owned worker cleaned up | R1: orphan, unlocked execution, stale status, ineffective cancellation marker |
| `publication` | Request/status scheduling barrier; second AppTest reader; one 0.01 s simulation after release | R2: FileNotFoundError, then normal completion |
| `notes` | Note-writer barrier; second JSON reader; no numerical execution | R3: visible incomplete JSON; original prediction preserved |
| `comparison` | Copies actual parity output into labeled disposable fixtures; deliberately conflicting metadata and one altered sample; no new simulation | R4/R6: three charts, no warnings/errors, changed sample plotted |
| `finalization` | One 0.01 s dynamic simulation; injected manifest hash-read OSError | R5: completed/error-null status despite missing manifest |

All modes exited 0 because their assertions reproduced defects. These are not product acceptance
passes. Scheduling barriers and hash-read faults were injected only through the review harness;
no delivered source, canonical equations, frozen configuration or historical result was patched.
Raw logs include the expected UI exception. Complete probe observations are embedded in
[`evidence.json`](evidence.json), with log/harness hashes and exact arguments.

The wall/RSS/output checks disappearing after supervisor loss are a source-based inference;
no greater-than-60-second or resource-exhaustion campaign was performed. Kernel CPU/file
limits were not claimed to disappear. The marked-running orphan record intentionally remains
as failure evidence; its worker and supervisor are no longer alive.

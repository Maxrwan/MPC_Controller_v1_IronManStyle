# Corrective review reproduction and retained evidence

Target **`219b9358409fa73fc59f24a7755da66771883e6b`**. See [decision](REVIEW.md),
[observations/hashes](evidence.json), [reader/ownership probes](review_probes.py), and
[launcher smoke harness](launcher_smoke.py). All source paths below refer to this exact pin.

## Isolation and source identity

The clean original checkout was at launcher descendant
`b49844c85b53ab3b77572156f4824689e7f80405`, branch `codex/apex-workbench-v0-1`.
An independent index/working directory reused local Git objects and the installed environment:

```sh
git clone --shared --no-checkout --local \
  /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle \
  /private/tmp/apex-workbench-review-219b935-20261027
git -C /private/tmp/apex-workbench-review-219b935-20261027 checkout --detach \
  219b9358409fa73fc59f24a7755da66771883e6b
ln -s /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/tools/apex_workbench/.venv \
  /private/tmp/apex-workbench-review-219b935-20261027/tools/apex_workbench/.venv
```

The clone-local exclude file hides only `/tools/apex_workbench/.venv`. Its tracked status is
clean. All 11 correction-record source hashes match. Test ROOT and apex imports resolve inside
this clone. No package installation/source edits occurred. The pre-Workbench-to-pin scientific
diff is empty for src/scripts/configs/tests/results and core dependency files.

Local retained evidence directory:
`/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/apex_workbench_correction_review_20261027/`.
Its name reflects the review start date; the report was completed on 28 October in Africa/Cairo.
Never overwrite it or rerun pytest with its retained basetemp. Use a new output directory for
any separately authorized repeat.

## Fresh combined invocation

Working directory: `/private/tmp/apex-workbench-review-219b935-20261027`.
The exact executed bootstrap, package versions, import paths and full arguments are in
`evidence.json` (`fresh_test_command`) and the first line of `fresh-tests.log`. Selection:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=.:scripts:src \
tools/apex_workbench/.venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q tools/apex_workbench/tests tests/unit/test_frenet.py tests/unit/test_baseline.py \
  tests/unit/test_runner.py --durations=8 \
  --basetemp=<FRESH_EVIDENCE>/pytest > <FRESH_EVIDENCE>/fresh-tests.log 2>&1
```

This shorter displayed bootstrap omits only the executed environment/import header print.
Actual result: **exit 1; 116 passed, 1 failed; 0 setup errors/skips; 50.89 s**.
Workbench: 48/49 pass. All 68 selected scientific tests and both entry-point/full-worker parity
checks pass freshly. The R1 no-cancellation variant fails at its immediate recovery assertion.
No rerun was used to replace that negative result. The earlier 99/18-error and final 49-pass
correction logs were read as historical evidence only.

Preflight found no active scientific/Workbench workload and no MEASURED_ACTIVE/D3_ACTIVE guard
files. Tests were sequential, with Accelerate SINGLE set before numerical imports; sampled
thread observations do not prove a precise active numerical thread count or timing guarantee.

## Review-only probes

The raw executed `review_probes.py` remains in local evidence. Its committed copy is formatted
but AST-identical; both hashes are recorded. Each mode was executed sequentially in a fresh
Python process from the pinned clone:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=.:scripts:src \
tools/apex_workbench/.venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import runpy,sys; sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name="__main__")' \
/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/apex_workbench_correction_review_20261027/review_probes.py \
<MODE> <EVIDENCE_ROOT> > <EVIDENCE_ROOT>/probe-<MODE>.log 2>&1
```

| Mode | Inputs/method | Executed observation |
|---|---|---|
| recovery | The just-failed R1 record; raw archive before reconciliation; one separate real dynamic worker with supervisor SIGKILL and no SIGSTOP; live unrelated process | Exit 0: interrupted/idempotent recovery, admission held until worker exit, unrelated process rejected by termination API |
| readers | Genuine completed dynamic seed from this fresh suite; two new unresealed copies; AppTest | Exit 0 means the expected defects reproduced: missing prediction KeyError; missing geometry silently renders partial trajectory, eight charts and zero errors/warnings |

The diagnostic recovery mode intentionally expects the retained failed-test layout. It is not
a general-purpose acceptance test; a new suite may not reproduce that scheduling failure. Do
not manufacture a failed assertion or relabel a successful run to satisfy its inputs.

Minimal C-R2 reproduction: copy a genuine completed run into a disposable fixture root, remove
only `request["prediction"]`, redirect the AppTest configuration's RUNS to that fixture root,
and execute the unchanged app. `list_runs()` admits it; the notes tab raises KeyError even
though plot request integrity checks already reject the changed request.

Minimal C-R6 reproduction: copy a genuine completed run into a separate fixture root, unlink
only `experiment/geometry.csv`, retain the original manifest/status, and execute both
`plots.trajectory(copy)` and AppTest. The direct figure has only `Plant trajectory`; the UI has
no missing-geometry error/warning. No scientific fixture is resealed or repaired for these probes.

## Exact launcher smoke and retained harness failure

The executable at the pin has SHA256
`8f66a97a554ddd8c6342ce6ffe9a5661e487599ac239c0a07af6f95ab7712cf7`.
The first sandboxed direct invocation could not bind loopback (EPERM); its generic busy-port
message is retained in the tool transcript. An authorized non-sandboxed direct invocation then
started the app. The later complete smoke command, run with local bind/process-inspection
permission from the original checkout, was:

```sh
tools/apex_workbench/.venv/bin/python -I \
  results/apex_workbench_correction_review_20261027/launcher_smoke.py \
  /private/tmp/apex-workbench-review-219b935-20261027 \
  /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/apex_workbench_correction_review_20261027 \
  > results/apex_workbench_correction_review_20261027/launcher-smoke.log 2>&1
```

The harness launches the unchanged command from `/private/tmp`, verifies its own listener PID,
health/HTML, repeat-launch rejection, and signals only its verified launcher helper. It allows
a bounded browser inspection window, ended by `launcher-stop.request`. Chrome tab 873261157
showed the working APEX page and labels. No experiment was submitted by the review browser actions.

The harness **exited 1** at the plain socket bind after shutdown (EADDRINUSE). It had already
confirmed server absence, but did not write its final summary or reach its missing-env section.
Do not report this as a completely passing harness. `launcher-ready.json`, server/busy logs,
the traceback and original harness are preserved. A separate follow-up established:

- Recorded owned helper and server PIDs no longer existed.
- A loopback connection returned errno 61 (refused).
- Binding with SO_REUSEADDR succeeded; immediate non-reuse bind is not equivalent to a live listener.
- An exact launcher copy in `launcher-missing-env/` returned exit 1 and the missing-setup/README
  message with no Workbench environment present.

Those observations are in `launcher-followup.json`; the missing-env stdout is retained separately.
The committed smoke harness preserves the failed assertion and is AST-identical to the executed
one. It is evidence, not a proposed launcher correction. No server is intentionally left running.

## Preservation and audit limits

`preservation_before.json` records 887 original tracked hashes and size/mtime for 13,376 old result
files. `preservation_after_tests.json` found zero changes. The final report/handoff audit permits
only this new review directory and the prepended handoff; previous handoff text remains a suffix.
Original failed-review/correction/launcher evidence remains unchanged. The separately observed
clone-local UI run during the interaction gap is untouched and excluded from review test totals.

This is bounded software review evidence on this Mac. Full resource exhaustion, power loss,
network-filesystem durability, real PID reuse and hardware/physical behavior are untested.
No implementation changes or formal acceptance were authorized by these checks.

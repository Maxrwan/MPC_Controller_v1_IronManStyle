# V0.2-B review reproduction and scope

Target: `895ecddf55754e94d5dbf53d5aca01f91f013a05`. Start status was clean; all execution below
preceded review-document edits. Source stayed pinned. Fresh root evidence directory:
`results/apex_workbench_v02b_review_20261028/` (ignored local evidence, hashes committed in
[review_record.json](review_record.json)). Do not rerun merely to combine test counts.

## Focused tests

From repository root, with no measurement guards/active benchmark, using the existing Workbench
environment and native SINGLE setup before numerical imports:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q tools/apex_workbench/tests \
--basetemp=results/apex_workbench_v02b_review_20261028/focused --durations=5
```

Retained execution: `focused.log`, exit 0, **127 passed in 46.29 s**. This is software review evidence,
not a timing benchmark or formal complete Verification. Refined clocks in provider unit tests did
not propagate a model; no refinement trajectories or 17-trajectory qualification campaign ran.
Use a fresh output path if a later authorized repetition is genuinely required.

## New independent nominal reference

`independent_parity.py` is a review-authored, retained script in the local evidence directory.
Its expected side constructs literal canonical VehicleParameters (all accepted populated fields;
unknown dimensions/rate stay null), direct ClosedTrack/circle_waypoints(5 m,128 points,0.6/0.9 widths),
DynamicBicycle with explicit linear/quasi-static components, and SimulationRunner. A test-only provider
returns 20 `[0,0]` commands followed by 80 `[0.020,0]` commands. Duration0.500 s, dt 0.005 s,
latency=None, target_laps=None, stop_on_boundary=False, seed [2,0,0,0,0,0]. It does not use lab
configuration/provider code for expected outputs. Canonical diagnostics and XY are evaluated from
the direct reference samples, and all state/control/diagnostic bytes and101 XY samples are compared.

The script acquires the existing lease/preflight, sets bounded CPU/file limits and native SINGLE
controls before numerical imports. The actual side calls the pinned nominal adapter once. It writes
only two nominal software-parity trajectories, not convergence, signal qualification or physical data.

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python \
results/apex_workbench_v02b_review_20261028/independent_parity.py
```

Retained original execution used the identical script under its temporary path; result is in
`independent-parity/result.json` and `independent-parity.log`, exit 0. The script refuses existing
output; do not delete prior evidence to make a rerun succeed. Full hashes are in the machine record.

## Adversarial record probes

`adversarial_records.py` (root), `confirm_findings.py` (root) and
`independent-context/probe_metadata.py` / `probe_partial_axes.py` (separate reviewer) are retained.
They copy genuine nominal records into fresh disposable directories and import only metadata
consumers; recorded `sys.modules` checks confirm no numerical model/library imports for these probes.

- Ordinary changed bytes/missing files keep original anchors and are rejected.
- Rebound-copy probes deliberately update the copied manifest entries and status manifest hash
  after changes, testing semantic/schema consistency under a faulty producer. Real source records
  are never rewritten. This is not a test of authentication against rewriting all retained evidence.
- C1 removes only the runner hash from each copied BASE/STEER source dictionary. On fresh pinned
  records both the worker source-check function and reader accept; pair remains a candidate.
- C2 changes copied diagnostics row 25 `a_cmd` to 1.0 while actual state/control remain 0; rederive the
  two copied summaries using the existing reporting function, then rebind. Reader accepts.
- C3 changes copied status/receipt to cancelled while keeping genuine full exported data and
  `horizon_reached=true`, then rebinds. Reader rejects the full-coverage cancellation fixture. This
  models an end-of-process failure window; no live cancellation race was launched or established.
- Consistent ten-row failed prefixes remain inspectable, with last time 0.045 s and no synthetic
  terminal row; they cannot become controlled candidates.

Root scripts select fresh review worker records. Separate-context scripts used retained WORK fixtures;
their worker-check probe met an unrelated later documentation-hash mismatch, so its result is not
evidence of worker admission. Root's fresh-record C1 confirmation resolves that limitation. A peer
inventory probe queried nonexistent `src/apex/track/geometry.py` and returned null; that is not a
missing-source finding. Actual track paths include `closed_track.py`, `centerline.py` and `synthetic.py`.

Peer raw outputs are preserved verbatim in `independent-context/`. Root confirmation results live
in `confirmed-findings/results.json`; the 15 general probes are in `adversarial/results.json`.

## Preservation

Before-review tracked SHA-256 and result size/mtime snapshot:
`/private/tmp/apex-workbench-v02b-review-20261028/before.json`.
The pre-WORK snapshot was also inspected for the recorded Finder metadata change. `.DS_Store`
metadata was not restored/edited. Neither metadata size/mtime checks nor source agreement are a
physical-validation claim. Implementation files remain at the pin; only this review package and
the prepended handoff are permitted delivery changes.

No qualification, new scientific cases, sweeps, full regression/Verification, canonical correction,
NMPC/async controller or hardware work is authorized by these reproduction instructions.

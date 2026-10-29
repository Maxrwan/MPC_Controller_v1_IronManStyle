# Engineering MVP — scope, gaps and composition

Revision/status meanings are defined in the [audit](ENGINEERING_CAPABILITY_AUDIT.md). The MVP is
one coherent **Run / Inspect / Compare / Replay** workspace with an engineering home, not another
set of specialized laboratories. It must make accepted work easier to use before adding science.

## Gap assessment

| Requested workflow / improvement | Classification | Smallest useful change |
|---|---|---|
| Unified home / discovery | **Missing** | Catalog supported adapters, recent/failed/quarantined records, owned execution state, guard/disk availability and evidence locations. Unavailable controllers are visibly unavailable. |
| Existing three experiment launchers | **Already sufficient** scientific execution; presentation **needs improvement** | Reuse exact `ADAPTERS`, validators/defaults, lab cases and `jobs.start_run`. Show configuration/source/units before launch; optional run note. No arbitrary parameters or new controller selector. |
| NMPC/TVLQR/async launch | **Scientifically gated** | Existing core does not constitute an approved W execution adapter. Defer new profile/execution contracts; offer later read-only archive inspection first. |
| Worker ownership, locks, resource limits, cancellation and retained outcomes | **Already sufficient** for accepted local scope | Reuse unchanged. Surface reasons; no UI-owned simulation loop or replacement queue. |
| History, filtering and reopening | **Exists but needs improvement** | Stable source-aware IDs, adapter/case/outcome/qualification filters, direct evidence links and explicit archived roots. Do not copy Q runs into the live folder to make them visible. |
| State/reference/control plots and geometry | **Exists but needs improvement** | Retain Plotly traces/units and source references; common selected time, useful overlays and available-channel selection. Never synthesize missing references. |
| Tracking error, effort/limits and diagnostics | **Exists but needs improvement** | Show existing summary fields and genuine control/diagnostic columns prominently. Distinguish track-relative error from packet-reference error. See the [metric backlog](CONTROL_ANALYSIS_BACKLOG.md). |
| Zoom / trace inspection | **Exists but needs improvement** | Keep normal Plotly interaction; add a deliberate linked inspection workflow. Independently rendered plots are not synchronized replay. |
| Two-run compatibility / lab qualification | **Already sufficient** decision engine | Reuse `comparison.eligibility` and qualification applicability; make Compare a primary workflow. Do not replace their labels with generic PASS. |
| More than two runs / comparison metrics | **Missing** | Pairwise classification matrix and overlays; display actual exported metric deltas with units/window/profile. No single multi-run causal ranking. |
| Prediction / learning notes | **Exists but needs improvement** | Prediction is already optional in code. Use engineering labels and optional analysis notes; retain original fields/append-only versions and learning access. |
| Raw evidence/provenance/logs and failure retention | **Already sufficient** backend; UI **needs improvement** | Outcome/evidence/coverage/numerics/window/excitation remain separate. Lead with termination reason and missing files; quarantine interpretation while preserving raw inspection. |
| Data export | **Exists but needs improvement** | Existing retained ZIP is useful but explicitly may contain unverified content. Add a selected verified-data/presentation package with clear source hashes and disclosure of unverified logs. |
| Reproducible figures | **Missing** as an explicit tested workflow | Export a clear standalone figure/HTML or evidence package with channel/units/window/plot settings and source references. No new reporting framework or implied image-export dependency. |
| Versioned recorded-data import / replay | **Missing** | Start with the existing Workbench bundle contract; deterministic seek/playback from retained samples/XY. Do not accept arbitrary CSV by guessed columns. |
| NMPC/async failure chronology viewer | **Missing** W integration; producer data **exists** | One explicit legacy software-archive profile first, including C0 and incomplete-output warnings; no generic “all archives supported” claim. |
| Raspberry Pi read-only monitoring | **Scientifically gated** producer contract | Plan one-way ingestion/recording; no command, arming or Safety-authority path. Physical clocks/frames/measurements require departmental contracts. |
| Advanced CT/observer analysis | **Scientifically gated** beyond existing verified outputs | Preserve C/F/S research gates. Do not display unexecuted research results as an accepted analytical dashboard. |
| One-click local launch | **Already sufficient** accepted mechanism | Retain owned listener checks, loopback binding, reuse, errors and shutdown. Any new presentation entrypoint needs launcher regression, not a new server framework. |

## Minimum composition

**Preservation constraint:** W's 56-file scientific inventory includes the current presentation
files. The recommended first stage adds a thin primary `workspace.py` and small presentation/catalog
modules; it leaves **all 56 files byte-identical**. The existing `app.py` remains a compatibility
entrypoint. The accepted launcher may target the new primary entrypoint with equivalent ownership
checks. This is one primary engineering workspace over the accepted engine, not new laboratory pages.
No import-time execution of the legacy UI is assumed; reuse its backend APIs and schemas directly.

`jobs.provenance()` already captures tracked tooling and tool-local Python modules, so added
presentation code must appear in the full run provenance. It does not replace the frozen scientific
inventory or change qualification application. New views must only render values from verified
readers/accepted summaries; no new scientific calculation is hidden in a presentation module.
New presentation code requires its own engineering review/Verification; being outside the old
inventory is not a verification claim. This proposal preserves existing enforcement, not an exception
to it. It depends on preserving all numerical construction, export, ingestion and evaluation code.
If implementation requires changing a frozen dependency, stop the qualification-inheritance claim
and use the separate decision in [D1](DECISIONS_AND_NEXT_TASK.md#scientific-decisions-only-when-needed).

Use a small non-authoritative catalog, rebuilt from explicit roots: the existing owned run root and
published Q reference directories. Discovery may read metadata; interpreting evidence still goes
through frozen readers. Imported/archived roots are read-only and never treated as live worker
ownership. No reconciliation/cancellation is invoked against arbitrary imported records. Logical
execution identity and path aliases are distinct; a directory copy is not another execution.

An inspection context contains source identity, lifecycle outcome, evidence state, available channels,
units, timebase/coverage, reference owner, geometry availability, existing metrics and event sources.
It is a view of original artifacts, not a replacement request, repaired manifest or new simulator.
Use optional fields as unavailable, never zero. Keep separate live-job controls and recorded playback.

For three selected Q runs BASE/IZ_HIGH/CF_HIGH, BASE→IZ and BASE→CF can be qualified edges; IZ→CF
is illustrative because two treatment factors differ. A shared overlay does not qualify the triad.
Reject invalid evidence before scientific plotting; raw diagnostic access must retain its warnings.

## Read-only recorded-data contract

The first import/replay profile is **existing Workbench retained evidence**, including its request,
receipt/status, manifest, telemetry contract, actual state/control/XY/geometry and optional diagnostics.
Validate versions, paths, hashes, SI units, monotonic native time and required coverage through existing
contracts. Preserve its scientific source and qualification references; do not infer missing identities
from the checkout. A wrapper may identify origin/profile and presentation annotations, not grant validity.

Seek by actual stored timestamps; show the selected native sample and its timestamp. Do not interpolate
states/position or shift time origins silently. ZOH controls are shown only under the producer's declared
interval semantics; the lab terminal control is informational. Missing optional events/references are
explicitly unavailable. Missing required data fails closed. Play speed is a viewer clock, not plant time.

Later legacy profiles must bind their own producer/schema/unit/time/reference definitions and retain
partial/censored fields. A profile for recorded synthetic fixtures is labeled synthetic. Physical
Perception/Embedded telemetry is a separate contract: canonical plant state is not a wire schema.
The MVP emits no actuator command, permission, cancellation acknowledgement or Safety transition.

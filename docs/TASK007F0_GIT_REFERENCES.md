# Task007F-0 — Accepted Performance Git preservation

Observed 19 October 2026. Repository: `Maxrwan/MPC_Controller_v1_IronManStyle`.
The initially clean checkout was on `main` at E4. No preexisting release/research branches or tag
were found locally or remotely. All three requested refs were created without moving an old ref,
pushed normally, and checked with `git ls-remote`. Work now resides on `research/efficiency`.
No extra worktree was created; existing ignored histories stayed in their original location.

| Reference | Identity and purpose |
|---|---|
| [release/performance-synthetic-v1](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/tree/release/performance-synthetic-v1) | Frozen accepted tracked snapshot, exactly `48adbdf64d492592d15e23c917aca71fa58aa8a5` |
| [performance-synthetic-v1](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/tree/performance-synthetic-v1) | Annotated tag object `76d9eaa65af02efb0263916adc75d5247a0e778f`; peeled commit `48adbdf64d492592d15e23c917aca71fa58aa8a5` |
| `research/efficiency` | Created from E4; contains subsequent specification-only delivery; future experimental work needs explicit authorization |
| `main` | Remains integration/default branch at E4 during F0; no default-branch change or automatic merging |
| Scientifically verified source/profile | `e603672b209985f11ed26b6f44d3949ffd5675c5` |
| E3 formal verification delivery | `ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9` |

The [E4 snapshot](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/tree/48adbdf64d492592d15e23c917aca71fa58aa8a5)
contains the acceptance overlay. It does not represent another scientific execution. The immutable
manifest hash remains `5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf`.
The tag annotation explicitly distinguishes the E2 source/profile, E3 verification and E4 decision.

## Protection verified

- [Branch ruleset 25418055](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/rules/25418055):
  **active**, exact `refs/heads/release/performance-synthetic-v1`, restrict updates/deletions and
  block force pushes, empty bypass list, no excluded refs.
- [Tag ruleset 25418590](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/rules/25418590):
  **active**, exact `refs/tags/performance-synthetic-v1`, restrict updates/deletions and block
  force pushes, empty bypass list, no excluded refs.

Both were created through authenticated repository settings, then verified through successful
read-only GitHub API ruleset GETs. GitHub reported `current_user_can_bypass=never` and the UI
showed one matching target for each. Initial account re-authentication was completed by the user;
there is no remaining protection blocker. The [compact record](task007f/f0/git_preservation.json)
retains returned rules/settings and exact refs. An optional effective-branch endpoint was rejected
by the connector URL validator; it is not presented as a successful check. No destructive push,
tag overwrite, ref deletion or security-bypass probe was performed.

These protections are enforced configuration, not a guarantee against future authorized
administrative changes. Future checks should re-read the rule objects, exact targets and bypasses.
Do not disable protections to conduct research; use the research branch. If settings ever need
manual restoration, choose Settings → Rulesets → **Active**, exact branch/tag pattern, empty bypass
list, **Restrict updates**, **Restrict deletions**, **Block force pushes**, then read back the saved
settings. Never target all branches or change the default branch for this purpose.

## Safe access and independent development

Read accepted files directly by the immutable commit URL. For a separate read-only investigation,
use a new detached worktree; the following are **instructions, not commands executed by F0**:

```sh
git fetch origin tag performance-synthetic-v1
git rev-parse 'performance-synthetic-v1^{commit}'
# Must equal 48adbdf64d492592d15e23c917aca71fa58aa8a5 before continuing.
git worktree add --detach ../APEX-performance-synthetic-v1 performance-synthetic-v1
```

For future Efficiency implementation, prefer an isolated worktree or separate checkout, with its
own environment and fresh evidence root. The current checkout already has `research/efficiency`
checked out, so do not try to check that same branch out twice. One safe reviewed option is a
new task branch from the research branch in another worktree:

```sh
git fetch origin research/efficiency
git worktree add -b codex/efficiency-approved-subtask ../APEX-efficiency origin/research/efficiency
```

Use a new authorized name/path; never overwrite an existing checkout. Audit status before switching
or merging. A separate clone can instead use `research/efficiency` independently. Do not copy ignored
raw histories into the new checkout without archival authorization. Reproduction also requires the
locked dependencies, documented native backend policy and actual fixture files; refs alone do not
install a scientific environment. Review and normally merge approved work into integration only
when authorized. Frozen refs never receive research commits, force pushes or tag replacements.

## Preservation limit

Git tracks source, fixtures, compact evidence and documentation. It does **not** preserve ignored
`results/`, `.venv`, installed solver binaries or machine state. F0 content-hashes tracked files and
checks the existing 294-entry scientific inventory; the 11,646 local result-file preservation entries
are **size/mtime metadata only**, not independently recomputed full-content hashes. No raw data were
added, deleted, relocated or rewritten. A separately authorized, independent content-hashed backup
of the scientific archive remains outstanding. Do not mistake a release branch/tag for that backup.

# Validation

## Reproduce the checks

From the repository root:

```bash
python3 -B skills/bot-orchestrator/scripts/test_board.py
python3 -B skills/bot-orchestrator/scripts/test_moa.py
python3 -B scripts/test_repository.py
python3 scripts/check_repository.py
python3 examples/local_demo.py
python3 examples/moa_demo.py
python3 scripts/validate.py --repeat 3 --output /absolute/path/to/new-validation-directory
```

No external account, model request, browser session, or package installation is needed for these commands.

## Behavioral coverage

The board suite covers:

- A complete two-task goal with actual files, submission, review, verification, and closure.
- Refusal to start before a dependency is accepted.
- Atomic rejection of unknown dependencies and missing deliverables.
- Separation of submission from acceptance.
- Detection of changed submitted and accepted files, including transitive ancestor artifacts and review records.
- Rejection at start, submit, accept, and resume when an accepted ancestor becomes stale.
- A 1,000-task chain without recursive graph traversal.
- Structured rejection of malformed current state, invalid schema types, missing references, and dependency cycles.
- Read-only next-action reports with evidence, conflict, budget, wait, and closed-goal behavior.
- Transitive invalidation and preserved history after reopening work.
- Two separate processes competing for overlapping declared write scopes.
- Timezone-aware due reminders that do not automatically resume work.
- Rejection of naive reminder times without a state change.
- Attempt budgets that do not reset through rework.
- Required cancellation remaining incomplete and cancelled optional work not blocking closure.
- Parent traversal and symlink escape rejection.
- Rejection of FIFO evidence without hanging on POSIX.
- Persistence across command processes and refusal to overwrite an existing board.

## MOA and repeated-validation coverage

The version 1.2.0 acceptance set contains **32 board tests, 30 MOA tests, and 7 repository-tool tests**. The MOA suite executes actual local subprocesses and covers:

- Proposal, cross-review, synthesis, declared criterion coverage, and repeated checks on the same candidate.
- A failed first synthesis repaired from actual feedback, with every failed observation retained.
- Exhausted rounds, flaky repetitions, and unchanged failed candidates stopping with `NO_PROGRESS`.
- Proposal quorum, explicit degraded operation, and failed critics blocking synthesis.
- Non-JSON responses, missing checks, nonzero exits, bounded streams, timeouts, and POSIX owned-descendant termination.
- Changed source inputs or candidates blocking acceptance and later audits.
- Verifier-only rechecking, immutable candidate digests, and stale-source refusal before new execution.
- Accepted-status edits, missing repeat receipts, and outside-run candidate references being rejected.
- Real calculations with different source values, queued adapter calls, and non-overwriting evidence directories.

The board tests additionally cover required-work ranking and advisory disjoint batches without changing the board revision. The repository tests execute both demonstrations using only copied standalone skill files.

`validate.py` runs the complete acceptance set, content checks, and both demonstrations for every requested cycle. Each raw log and exit code is retained in the new output directory. It stops at the first failed check, records unfinished work honestly, and verifies that the source fingerprint did not change during the campaign. `report.json` is the authoritative local run record. Published release notes distinguish observed campaigns from this reproducible test specification.

The offline MOA adapters are deterministic local programs. Their model call count is zero. They establish callable process routing and validation behavior, without establishing external model quality or native host-agent integration.

## Previous observed baseline

Version 1.1.0 was checked locally on macOS with Python 3.9.6:

| Check | Observed result |
| --- | --- |
| Board behavioral suite | 30 tests passed, no failures or skips. |
| Repository-tool suite | 6 tests passed, no failures or skips. |
| Repository content checker | Required files, links, English text, version consistency, and Python 3.9 syntax passed. |
| Repository demonstration | Actual files, checks, reviews, verification, and goal closure completed. |
| Standalone skill demonstration | Completed using only a copied skill directory, exercised by the repository-tool suite. |
| Legacy board compatibility | A board created and accepted by the published v1.0.0 helper was read, verified, and closed by v1.1.0. Read-only queries preserved its payload. |
| Skill entry-point format | Passed the available skill format validator. |

The repository-tool suite exercises successful installation, overwrite refusal, direct and symlink-resolved self-copy refusal, missing publication files, invalid publication content, and the standalone demonstration.

The initial 1.0.0 baseline had 16 board tests. These counts describe actual local runs. They do not represent GitHub CI, independent review, or acceptance on another platform. Release preparation retains the exact local command output outside the public source tree.

## Not verified by those checks

- Native import and invocation in every possible bot host.
- A host model following every instruction correctly across all tasks.
- Real multi-agent delegation, external account actions, or scheduled wake-ups.
- Linux or Windows native execution from the macOS baseline alone.
- Business correctness solely from matching local file hashes.

Host integrations and new platforms should contribute their own reproducible acceptance records with versions, actual actions, outputs, and limitations.

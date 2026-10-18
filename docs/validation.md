# Validation

## Reproduce the checks

From the repository root:

```bash
python3 -B skills/bot-orchestrator/scripts/test_board.py
python3 scripts/check_repository.py
python3 examples/local_demo.py
```

No external account, model request, browser session, or package installation is needed for these commands.

## Behavioral coverage

The board suite covers:

- A complete two-task goal with actual files, submission, review, verification, and closure.
- Refusal to start before a dependency is accepted.
- Atomic rejection of unknown dependencies and missing deliverables.
- Separation of submission from acceptance.
- Detection of changed submitted and accepted files.
- Transitive invalidation and preserved history after reopening work.
- Two separate processes competing for overlapping declared write scopes.
- Timezone-aware due reminders that do not automatically resume work.
- Rejection of naive reminder times without a state change.
- Attempt budgets that do not reset through rework.
- Required cancellation remaining incomplete and cancelled optional work not blocking closure.
- Parent traversal and symlink escape rejection.
- Rejection of FIFO evidence without hanging on POSIX.
- Persistence across command processes and refusal to overwrite an existing board.

## Observed baseline

The original helper baseline was run locally on macOS with Python 3.9.6: **16 tests passed**, no failures. The initial documented local demonstration completed successfully, and the skill entry point passed its format validator.

The English publication package is rechecked before publishing. Its exact command output and artifact summary are retained in the release preparation record; do not convert that local evidence into a claim about a remote CI run.

## Not verified by those checks

- Native import and invocation in every possible bot host.
- A host model following every instruction correctly across all tasks.
- Real multi-agent delegation, external account actions, or scheduled wake-ups.
- Linux or Windows native execution from the macOS baseline alone.
- Business correctness solely from matching local file hashes.

Host integrations and new platforms should contribute their own reproducible acceptance records with versions, actual actions, outputs, and limitations.

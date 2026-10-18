# Troubleshooting

## The host does not list the skill

Check that the complete `bot-orchestrator` folder is in the host's documented skill location, with `SKILL.md` at its root. Refresh discovery or start a new session. Invocation syntax and discovery rules are host-specific.

## The installer says the destination exists

It intentionally refuses to overwrite user changes. Inspect or back up the existing directory, choose another explicit destination, or remove only the version you intended to replace. Do not delete task workspaces as part of a skill upgrade.

## DESTINATION_INSIDE_SOURCE

Choose a destination outside `skills/bot-orchestrator`, including when the path traverses a symlink. Installing a directory into itself would recursively copy it. The installer rejects this before creating the target.

## INVALID_BOARD_STATE or UNSUPPORTED_SCHEMA

Preserve the database. Check that it belongs to this goal and came from a supported board version. If you have a known-good backup, inspect it separately; do not overwrite the failing evidence or edit task status, digests, or attempt counts to make the command succeed. Version 1.1.0 accepts structurally valid schema version 1 boards and does not perform an automatic migration.

## How to choose a task after an interruption

Run `next` for actionable candidates, wait conditions, and blockers, then inspect the referenced artifacts and real host execution handles. The query does not change the revision. A ready candidate is not reserved; starting another task may change its write-conflict outcome.

## BOARD_EXISTS

Use the existing board's status command. Initialize a different explicit database only for a different goal. Do not overwrite a board to clear a difficult state.

## DEPENDENCY_PENDING or DEPENDENCY_CHANGED

A direct or transitive input is unaccepted or its pinned artifact or review files changed. The error identifies the first affected dependency. Inspect the actual input and relevant review. Restore valid upstream acceptance before resuming its consumers; do not edit stored digests manually.

## WRITE_CONFLICT

A running or review task has an overlapping declared path. Inspect the true executor state and let its review settle, or replan ownership. Do not bypass the conflict by inventing a second path that points to the same resource.

## EVIDENCE_UNREADABLE, INVALID_EVIDENCE, or EVIDENCE_CHANGED

Confirm that the reference is a workspace-relative regular file, readable, within 64 MiB, and still the accepted revision. Use versioned intermediate artifacts rather than a mutable working file shared across stages. Preserve the mismatch and repeat the meaningful review if the change was legitimate.

## ATTEMPT_BUDGET

The task has consumed its permitted starts. Diagnose the repeated cause and revise the plan with a concrete changed condition. Do not reset counters or create duplicate work solely to hide the exhausted budget.

## A reminder is due, but nothing ran

That is expected. `due` is a query. The helper does not schedule execution. Inspect the real missing condition and resume explicitly, or use an actual host scheduler when the user requested one.

## A task says running after the session ended

Inspect the host's real execution handle. The board is a persistent record, not a process supervisor. Record the actual wait, blocker, cancellation, or submission after inspecting it.

## MOA spec or adapter failure

Use `moa.py inspect` to check commands, source files, criterion coverage, and maximum calls before execution. Examine the failing call's request/stdout/stderr and actual exit code in `result.json`. The driver expects one UTF-8 JSON object on stdout; diagnostic prose belongs on stderr.

`PROPOSAL_QUORUM` means too few valid proposals. `CRITIQUE_EXECUTION` and `VERIFICATION_EXECUTION` mean a required stage failed to execute correctly; they are not successful business checks. `ACCEPTANCE_FAILED` retains the actual negative check results. `NO_PROGRESS` means the same failed candidate digest returned again; inspect the repair rather than resetting history.

For `INPUT_CHANGED` or `EVIDENCE_CHANGED`, preserve the run and establish the actual input/candidate revision. For `ADAPTER_TIMEOUT`, `RUN_DEADLINE`, or `CLEANUP_UNKNOWN`, inspect real execution and any remote receipt before retrying. Use a new directory for every run or recheck.

## MOA passed locally, but the wider task is incomplete

The MOA result covers its declared candidate and checks. Verify the intended final artifact, integration, destination, and user acceptance before reviewing or closing the wider goal. The offline demo validates deterministic local process adapters and makes no model calls.

## An external request timed out

Query the original operation or idempotency receipt before repeating an effect. If no reliable confirmation exists, preserve the uncertain result and explain it. A local state transition cannot determine whether a remote message or submission happened.

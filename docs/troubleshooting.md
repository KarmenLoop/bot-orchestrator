# Troubleshooting

## The host does not list the skill

Check that the complete `bot-orchestrator` folder is in the host's documented skill location, with `SKILL.md` at its root. Refresh discovery or start a new session. Invocation syntax and discovery rules are host-specific.

## The installer says the destination exists

It intentionally refuses to overwrite user changes. Inspect or back up the existing directory, choose another explicit destination, or remove only the version you intended to replace. Do not delete task workspaces as part of a skill upgrade.

## BOARD_EXISTS

Use the existing board's status command. Initialize a different explicit database only for a different goal. Do not overwrite a board to clear a difficult state.

## DEPENDENCY_PENDING or DEPENDENCY_CHANGED

A required input is unaccepted or its pinned files changed. Inspect the actual input and relevant review. Restore valid upstream acceptance before resuming its consumers; do not edit stored digests manually.

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

## An external request timed out

Query the original operation or idempotency receipt before repeating an effect. If no reliable confirmation exists, preserve the uncertain result and explain it. A local state transition cannot determine whether a remote message or submission happened.

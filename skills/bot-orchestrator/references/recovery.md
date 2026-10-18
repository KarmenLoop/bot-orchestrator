# State and recovery

## Task states

| State | Meaning | Next condition |
| --- | --- | --- |
| pending | Recorded but not started | Accepted dependencies, valid inputs, and no resource conflict. |
| running | An execution start is recorded | Actual submission, or an explicit wait/block/cancellation. |
| review | Output and evidence submitted | Accept after inspection, or return precise rework. |
| waiting | A specific external condition is missing | Inspect the actual condition, then resume explicitly. |
| blocked | The current path lacks a requirement or an upstream result is invalid | Resolve the requirement and recheck upstream work. |
| done | The submitted revision was accepted | Reopen when relevant inputs or artifacts change. |
| cancelled | This branch will not advance | Resume only within the user's actual renewed request. |

The board is a record. A running label does not prove a live process, and cancellation does not stop one. A done label records an acceptance decision, not a proof of business correctness. Inspect or cancel real execution through the host before recording the corresponding transition.

## Checkpoint

Before a task switch, wait, context limit, or interruption, persist:

```text
Goal: the user-level result.
Confirmed: requirements, authority, constraints, and important decisions.
Delivered: artifacts, versions, acceptance results, and evidence references.
In flight: real handles and observed stage; unknown if no reliable handle exists.
Waiting: the exact condition and whether a real schedule receipt exists.
Risks: uncertain external effects, failures, and unrun checks.
Next: one concrete action and its prerequisite.
```

Keep secrets, full private transcripts, and large logs out of checkpoints. Use retrievable references. If a reference is no longer accessible, mark its facts unverified rather than reconstructing details from an old summary.

## Resume sequence

1. Locate the persistent record for the requested goal, not a similarly named old project.
2. Read the latest user corrections and pause/cancellation state. Identify the scope actually being resumed.
3. Read the task board and relevant artifacts. The board's verify command detects local reference changes, not external outcomes or content correctness.
4. Inspect original execution and external-operation handles. Do not replay completed effects. An absent success record is not evidence that an effect did not occur.
5. Recheck necessary current host capabilities and identity. Chat summaries do not restore account sessions, file handles, device permissions, or approval grants.
6. Continue the first genuinely actionable task and persist the basis, remaining uncertainty, and next step.

## Invalidate changed inputs

When a source, interface, or accepted output changes, identify downstream consumers. Block affected work and preserve old outputs as history rather than current evidence. After upstream acceptance is restored, inspect the difference before resuming or accepting downstream work.

The board's reopen operation returns an accepted task to pending and blocks noncancelled descendants. It does not stop their real processes. Notify or cancel those executors first so they do not keep producing work from stale inputs.

## Retry and cancellation

Record the last observation, failure class, changed condition, duplicate-effect risk, and remaining budget before a retry. Unchanged inputs and unchanged conditions do not justify an unlimited loop.

A pause stops new dispatch. A resume continues the existing goal rather than creating a duplicate. A cancellation retains already-created artifacts and external effects, with truthful cleanup results; deleting them requires the relevant scope.

## Compact handoff with a real next action

A checkpoint should let another session act without rereading every message. Keep the task contract in a workspace document and reference it from the board's goal or task notes. The board does not have separate authorization, process-handle, or scheduler fields; those facts belong in this checkpoint and the host's actual records.

```text
Goal: Deliver output/report-v2.md with checked source-linked figures.
Contract: goal-contract.md; latest user correction recorded under Decision 4.
Board: board.sqlite3, revision 14; report is waiting, facts is accepted.
Accepted input: output/facts-v2.json; digest recorded in the facts submission.
Actual execution: No live executor; last export finished and was read back.
Wait: Source B must confirm its revised total; no scheduled wake-up exists.
Unknown effects: None observed. No external report has been sent.
Next: Inspect Source B's reply, compare its figures to facts-v2.json, and
      reopen facts if the accepted values changed. Otherwise resume report.
Verify: Recompute each reported total and retain the comparison result.
```

Use real values from the current task. Do not copy the example's completion statements into a live checkpoint. Keep any actual source or operation identifier available through its authorized retrieval path.

When context becomes constrained, checkpoint before loading another large result. Load the contract, current next-action report, relevant source slices, and the one task's evidence. Summarization must preserve failed checks and the latest correction; it must not convert an unknown effect into a failure or a successful effect.

## Recovery decision table

| Observation after inspection | Concrete next action |
| --- | --- |
| Pending work appears ready | Check its card and input versions, then start it; the transition rechecks conflicts and budget. |
| A running record has a live host handle | Reattach through the documented interface; do not start a duplicate executor. |
| A running record has no reliable handle | Inspect artifacts and operation receipts. Record a blocker while the outcome remains unknown. |
| A review record has unchanged artifacts | Perform the actual acceptance checks and retain a review file; do not start it again. |
| A waiting timestamp is due | Check the missing condition; resume only when it is actually satisfied. |
| An accepted ancestor's file or review changed | Settle affected real executors, reopen that accepted task, and review the new version before resuming descendants. |
| The attempt budget is exhausted | Preserve the failure and explain what changed in the plan. Do not reset counters or clone a task solely to obtain retries. |
| Current state is malformed | Preserve the database and inspect a known-good copy; do not initialize over it or silently repair success history. |
| The board is closed | Verify evidence and the user's current intent; reopen only the accepted work that requires a new revision. |

A readiness report checks local workflow conditions. The coordinator must still verify actual permission, input meaning, external resources, and user-level acceptance.

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

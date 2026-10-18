# Local task board

## Purpose and boundaries

scripts/board.py persists a goal, tasks, dependencies, declared write scopes, submissions, reviews, waits, and events using SQLite transactions. It runs on Python 3.9+ with no third-party packages.

It does not execute work, call models, create workers, send messages, authenticate reviewers, or schedule jobs. Owner and reviewer fields are labels. File hashes validate references, not correctness or honest execution. Prefer an existing suitable host task store rather than duplicating it.

The coordinator normally writes the board and receives artifacts from workers. SQLite serializes local writers; it does not provide distributed ownership, cross-device sync, or process leases.

## Initialize an explicit board

```bash
python3 /absolute/path/to/bot-orchestrator/scripts/board.py --db /absolute/path/to/job/board.sqlite3 init --workspace /absolute/path/to/job --goal 'Deliver a checked fact table and report' --acceptance 'Sources retained, values checked, files read back'
```

The workspace must already exist. init refuses to overwrite a board. Later commands use the workspace saved in that board, regardless of the current shell directory.

In the command summaries below, board means Python, the script's actual absolute path, --db, and the actual database path. It is not an installed executable alias. Run `python3 scripts/demo.py` from the skill directory for a complete runnable walkthrough. The repository also exposes it as `examples/local_demo.py`.

## Add and start tasks

```text
board add extract --objective "Extract facts" --check "Each fact includes its source" --deliverable output/facts-v1.json --write output/facts-v1.json
board add report --objective "Write a consistent report" --check "Report values match the fact table" --deliverable output/report-v1.md --depends extract
board start extract
```

Repeat --deliverable, --write, or --depends for multiple values. Dependencies must already exist when a task is added, so unknown forward references and cycles are impossible. Existing cards are not silently overwritten; record a changed scope through explicit cancellation and a new card when appropriate.

The default owner is current-agent. --max-attempts defaults to 3 and may be set from 1 through 20 when the plan justifies it. Each start consumes an attempt; rework, resume, and reopen do not reset the budget. Re-diagnose and replan when the limit is exhausted.

Paths are workspace-relative. Absolute paths, parent traversal, and paths escaping through a symlink are rejected. --write . declares the whole workspace. A running or review task holds its declared write scope; overlapping paths block another start. This is coordination, not a filesystem sandbox.

For iterative edits, submit immutable version snapshots or patches rather than repeatedly pinning the same mutable final file. Later legitimate edits would otherwise invalidate a previous stage's reference. Accept the final working artifact in an integration task.

## Submit and review

After actually creating the deliverable and performing the checks:

```text
board submit extract --evidence evidence/extract-check.txt --note "Source checks executed; awaiting review"
board review extract --decision accept --evidence evidence/extract-review.txt --reason "All facts retain valid source locations" --reviewer self
```

submit reads all declared deliverables and supplied evidence, storing paths, byte lengths, and SHA-256 digests. It moves the task to review, not done. Files must exist, be readable regular files, and be no larger than 64 MiB. Split large logs or supply a useful bounded check record; file contents are not copied into the board.

accept rechecks submitted files and the full transitive dependency chain, including accepted review files, and pins a real review record. Start, submit, and resume also validate that entire chain. An unchanged direct parent cannot hide a changed ancestor. It cannot decide business correctness on your behalf. Use self for self-review and never invent an independent reviewer.

For a failed check:

```text
board review extract --decision rework --evidence evidence/problems.txt --reason "Fact 7 lacks a source; correct it and recheck"
```

The task returns to pending. Start, fix, submit, and review again. Review history remains recorded; do not turn a mismatch into a pass by replacing the stored digest manually.

## Wait, block, cancel, and resume

```text
board mark report --state waiting --reason "Waiting for source confirmation" --wake-at 2026-10-20T09:00:00+08:00
board due
board resume report --reason "The source confirmation actually arrived"
board mark report --state blocked --reason "Upstream facts conflict"
board mark report --state cancelled --reason "User cancelled; real execution has been settled"
```

wake-at applies only to waiting and requires an explicit timezone. due lists reminder times that have arrived; it neither schedules execution nor changes state. Resume only after inspecting the real condition. An event-based wait may omit a timestamp.

Cancel or settle real execution first. Cancelling an upstream task blocks its descendants. Cancelling required work does not satisfy goal acceptance; close will still fail. If the user reduces the goal, preserve the old contract and establish an accurate revised contract rather than rewriting success history.

## Inspect the next action

```text
board next
board next --limit 3
board next --now 2026-10-20T01:00:00Z
```

`next` opens the database read-only and preserves the revision. It returns:

| Field | Interpretation |
| --- | --- |
| ready | Pending task IDs that pass current dependency evidence, attempt budget, and declared write-conflict checks. |
| rankedReady | Ready candidates ordered by reachable unfinished required cards, including themselves; ties preserve insertion order. |
| requiredWorkReachable | The count behind each ready candidate's advisory ranking. |
| recommendedBatch | Up to `--limit` candidates with nonoverlapping declared write scopes; default 2, maximum 16. |
| blocked | Pending or explicitly blocked tasks, with the first blocking code and reason. |
| inFlight | Running and review records to inspect through the host; these are not liveness checks. |
| waiting | Wait reasons, optional timestamps, and whether a timestamp is due at the supplied or current time. |
| evidenceIssues | Changed or missing current submission, accepted review, or closure files. |
| goalAction | Continue, inspect changed evidence, review goal acceptance, or inspect an already closed goal. |

The ready list and recommended batch are snapshots, not reservations. Ranking supplies no duration, urgency, cost, or external-resource estimate; apply coordinator judgment from the actual goal. Two pending tasks can both be ready yet share the same write scope: starting one will block the other. Every `start` rechecks under its own write transaction. File hashes are cached only within the current inspection; later commands read files again.

A blocker is diagnostic; this query does not change a task to blocked or clear a wait. An unrelated stale artifact does not automatically stop independent ready work. `review_goal_acceptance` is a prompt to inspect the original contract, not permission to close a goal or a guarantee that required work passed.

For a context handoff, save the report's revision, artifact references, unresolved effects, and one next action in your goal checkpoint. Do not paste a private board into public logs.

## Verify and reopen

```text
board verify
board reopen extract --reason "Input revision changed; extraction needs a new review"
board status --full
```

verify recomputes current artifact and review digests, including goal closure evidence, and exits 1 on changes or missing files. It does not verify online resources, code behavior, or the truth of a log, and it cannot guarantee that files will never change later.

reopen applies to done tasks. It preserves the previous submission and reviews, returns the task to pending, blocks noncancelled descendants, and reopens a closed goal. It does not cancel real downstream processes. After new upstream acceptance, inspect differences before resuming each affected task.

## Close a goal

```text
board close --evidence evidence/final-check.txt --reason "User-level conditions checked and artifacts read back"
```

At least one required task must exist. Required tasks must be done; optional tasks must be done or cancelled; current evidence must still match. Use add --optional only for work that genuinely is not required by the goal. Do not recategorize missing deliverables to hide an incomplete outcome.

status returns a summary. readyByDependency lists pending candidates based on dependency states only; start still checks evidence, attempts, and write conflicts. status --full includes the raw state and event history. Do not store secrets in it.

Closed boards reject further changes. Reopen accepted work when its input changes, or initialize a separate board for a different goal.

## State integrity and compatibility

Schema version 1 is retained in version 1.1.0. Existing valid version 1 boards remain readable without rewriting or migration. Current-state shapes, paths, file records, task references, dependency cycles, budgets, and accepted-state requirements are validated before executing a command. Malformed state produces `INVALID_BOARD_STATE`; an unsupported or incorrectly typed version produces `UNSUPPORTED_SCHEMA`. These errors do not repair or overwrite the payload.

This checks structural consistency. Local database owners can still modify records; the board does not authenticate reviewers, prove historical events, or act as an authority for execution. Preserve a failing database and inspect a known-good copy rather than editing counters or hashes to bypass a gate.

## Results and checks

Normal outputs are JSON. Exit 0 means the command succeeded, exit 1 means verify found changed references, and exit 2 means invalid input, state, conflict, or I/O/format failure.

Run python3 -B /absolute/path/to/bot-orchestrator/scripts/test_board.py after changing the helper. Tests create isolated temporary workspaces and cover real file reads, lifecycle transitions, separate-process write conflicts, evidence changes, reminder timezones, and recovery. Passing them does not validate a host's model, workers, connectors, or scheduler.

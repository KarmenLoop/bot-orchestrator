# Architecture

## Responsibilities

The **user** defines the goal, constraints, authority, and relevant preferences.

The **coordinator** retains the goal, chooses actionable work, manages dependencies, receives outputs, and makes evidenced acceptance decisions.

An **executor** performs a bounded task through real host tools. It can be the coordinator itself, an authorized collaborator, or a specific documented tool. The skill does not require multiple agents.

The **host** owns tool availability, account sessions, execution permissions, cancellation interfaces, and optional scheduling. These are never manufactured by the board.

The **board** records the workflow. Its transitions are explicit command invocations and do not cause external work.

The optional **MOA driver** executes declared command adapters through proposal, critique, synthesis, and repeated-verification stages. It pins inputs and stage evidence, bounds concurrency and rounds, and checkpoints actual execution receipts. It is separate from the record-only board.

The **artifact workspace** holds deliverables and evidence. The board stores references and digests rather than copying their contents into every context.

## Data and transactions

A board has schema version 1, one workspace, a goal and acceptance statement, an overall status, a revision, tasks, events, and optional closure evidence.

The SQLite database contains one board record serialized as JSON. Each mutation begins a local immediate transaction, reads the current record, validates current-state integrity and the requested transition, updates the record, and commits. Invalid transitions leave the prior revision intact. SQLite serializes competing local writes; this is not a distributed coordination system.

Task dependencies may refer only to cards already in the board. Append-only dependency edges therefore cannot introduce a cycle. The current helper does not edit existing dependency lists in place. The loader also rejects missing references or cycles introduced by direct database edits. Schema version 1 remains unchanged in release 1.1.0.

## Evidence

Each pinned local file records its relative path, byte count, and SHA-256 digest. Submissions pin deliverables and check records. Acceptance rechecks the submitted revision and pins the review record. Goal closure pins its own user-level acceptance record.

Use versioned deliverables or patches for intermediate stages. If successive tasks repeatedly edit the same pinned file, an earlier reference correctly becomes stale. The final working artifact can be reviewed by a separate integration task.

Before start, submit, accept, or resume, an iterative traversal rechecks every accepted ancestor, including review evidence. The `next` query uses the same start preflight without a state transition and hashes each referenced path once per inspection. It does not allocate a lease or claim that an execution record is alive.

Files are not immutable simply because they were hashed. `verify` detects later changes when invoked. It does not prove the truth of a log or the correctness of the content, and it cannot make a check and a future filesystem mutation atomic.

## Declared write scopes

The board rejects starts when a running or review task holds a matching or overlapping declared path. A directory scope overlaps its descendants, and `.` overlaps the workspace.

This reduces accidental concurrent writes among cooperating callers. It is not an OS permission boundary, a resource lock for external services, or proof that a caller obeys the declared scope. Real isolation belongs to the host.

## Recovery and invalidation

Task starts, submissions, reviews, waits, and other transitions survive separate process invocations. Reopening accepted work preserves its prior submission and reviews and blocks noncancelled downstream tasks. A closed goal becomes open again.

Actual processes and external operations are separate. Before a resume, inspect their real handles and settle uncertain effects. Do not repeat a message or submission merely because the local board has no success record.

## MOA refinement and evidence

Each accepted MOA candidate must pass every declared verifier for all configured repetitions on its exact digest. Failed candidate digests cannot be retried in another refinement round without a changed version. Declared critic failures stop synthesis; proposal failures are tolerable only under an explicit reduced quorum and are reported as degradation.

`recheck` audits an accepted source run and executes only its verifiers in a new directory, retaining the candidate hash and source-result reference. `audit` executes no commands and checks hashes plus accepted-stage identities, JSON receipts, criterion coverage, and repeated-check completeness. Local record owners can still forge a complete history; these records are not authenticated attestation.

The board's next-action report additionally ranks candidates by reachable unfinished required work and chooses an advisory batch with disjoint declared writes. It acquires no lease and does not estimate durations or override host/user decisions.

## Limits kept outside the core

Model selection, account management, cross-device sync, host-agent spawning, timers, notifications, remote process control, and execution sandboxes remain outside these helpers. The MOA driver only supervises commands it directly starts. Integrations should adapt the existing host interface rather than treating the board as a new authority for those capabilities.

# Orchestration decisions

## Choose a pattern from the work

| Actual need | Pattern | Completion condition |
| --- | --- | --- |
| One bounded action with an available tool | Direct execution | The requested result is read back or otherwise observed. |
| Each output consumes the preceding output | Sequential tasks | Every consumed revision is accepted before the next task. |
| Complementary outputs can be produced independently | Dependency graph | Each branch passes its checks, then integration passes the user's checks. |
| Several approaches to the same bounded question could expose mistakes | MOA proposal, critique, synthesis | One integrated candidate passes the declared criteria and repeated verification. |
| A result needs another perspective | Targeted review | Findings are resolved against evidence; disagreement remains visible until resolved. |
| A necessary event or authorization is missing | Explicit wait with independent work | The actual condition arrives and is inspected before resume. |

Use the simplest pattern that reaches the result. Extra proposals add cost and correlated errors when all participants see the same incomplete evidence. MOA is especially useful for competing approaches or interpretations; complementary implementation tasks usually benefit from a dependency graph and a single integration owner.

## Test feasibility before expanding the plan

For each required acceptance criterion, establish:

1. **Input:** the actual source or resource is accessible and its version is known.
2. **Action:** a documented tool can perform the operation within current scope.
3. **Observation:** an executable check or accountable review can distinguish success from failure.
4. **Delivery:** the final artifact can reach the user's intended destination.
5. **Budget:** time, attempts, context, concurrency, and external costs fit the available limits.

For an uncertain interface, run the smallest representative slice before dispatching dependent work. Examples include exporting one record and reading it back, executing one adapter packet, or querying the intended account's actual resource. Preserve the observation; a tool appearing in a list is not that observation.

If one criterion lacks a viable path, record its exact missing condition and advance independent work. If it determines the whole goal, explain the concrete gap or revise the deliverable with the user rather than creating more tasks that cannot succeed.

## Plan backward from delivery

Start with the final acceptance and identify the inputs it consumes. Create tasks only for outputs that need a distinct owner, check, version, or execution boundary. A planning document itself should not become a dependency for every action unless those actions actually consume it.

For each card, include its acceptance-to-evidence mapping in the task's check field or a referenced contract. Keep negative constraints and current user corrections beside the affected card. Define the integration check before branches diverge.

Preserve versioned intermediates. Repeatedly editing a previously pinned shared file will invalidate its earlier acceptance; immutable snapshots or patches make that dependency explicit.

## Select the next useful work

1. Remove candidates with unaccepted or changed ancestors, exhausted budgets, or conflicting active write scopes.
2. Prefer work that feeds outstanding required deliverables, or resolves a concrete uncertainty likely to invalidate the plan.
3. Select only as much parallel work as the actual executor, context, and resource budget can support.
4. Keep one writer for integration. Account for shared external resources even when local paths differ.
5. Recompute after acceptance, rework, changed input, a user correction, or an external event.

The board's `next --limit N` provides an advisory `rankedReady` list and `recommendedBatch`. Ranking counts reachable unfinished required cards, including the candidate itself; ties preserve insertion order. The batch greedily avoids overlapping declared write scopes and defaults to two candidates. It is a snapshot, not a reservation, estimated critical-path duration, or permission to dispatch. User urgency, missing external resources, actual cost, and host rules still require coordinator judgment.

## Keep the execution loop evidence-driven

Observe the current state, choose one useful transition, execute it through the real interface, inspect the result, and update the next action. Follow existing operation handles through the host's wait or status mechanism. A new worker should not replace an already-running operation merely because its progress is inconvenient to inspect.

When a result fails, identify the specific unmet criterion and new evidence before deciding between repair, an alternative method, waiting, or stopping. Distinguish:

- A changed candidate that needs fresh checks.
- A transient observation that can safely be repeated within budget.
- An uncertain effect that needs its original receipt inspected.
- A blocked path that currently cannot achieve acceptance.

A broader plan can change as evidence arrives. Preserve accepted unaffected work and failure history; revise only the consumers affected by the change.

## Verification policy

Choose checks before examining a favorable result. Map every required criterion to evidence. For code, verify the relevant behavior and integration; for analysis, check source coverage and calculations; for file delivery, read back the actual destination.

Repeat the checks on one pinned candidate when flakiness or repeated validation matters. Retain every attempt, input version, exit code, and observation. A failed attempt remains a failed observation. When the candidate changes, start a new verification set for that version.

The MOA driver requires every declared verifier and every configured repetition to pass on the same candidate. A previously failed candidate digest cannot be revalidated in another refinement round without a changed candidate. A separate failed recheck remains evidence requiring resolution; a later pass does not erase it.

## Deliverability gate

Before claiming delivery, compare the user's original contract and latest correction to the actual destination, accepted revision, relevant checks, and settled execution resources. MOA acceptance concerns its bounded candidate and declared checks; it does not automatically deploy a change, send a file, or close the wider task board.

A later failed recheck of an accepted result should reopen the affected board card and invalidate its consumers after real executors are settled. The caller owns that transition; the MOA driver preserves receipts without rewriting unrelated task state.

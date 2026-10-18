# Execution and collaboration

## Choose an execution mode

Execute directly when the current agent has the tools and a handoff would cost more than the work. Batch independent reads and transformations when the host supports it. Use collaborators only for independently reviewable outputs with compact inputs, and only when both the host and current authorization permit delegation.

Different model names do not establish useful roles. An additional executor should contribute a real tool, domain skill, independent review, or nonconflicting parallel work. Do not require a fixed number of agents.

Keep one coordinator for the goal. A worker owns its bounded output; receiving a task does not authorize it to change the goal, contact new recipients, expand write scope, or delegate again.

## Task card

```json
{
  "id": "extract",
  "objective": "Extract traceable facts from the three specified inputs",
  "inputs": ["inputs/a.md", "inputs/b.md", "inputs/c.md"],
  "deliverable": "output/facts-v1.json",
  "acceptance": "Every fact retains its source location and uncertainty; conflicting claims remain separate",
  "depends": [],
  "owner": "current-agent",
  "writes": ["output/facts-v1.json"],
  "constraints": ["Read inputs without modifying them", "Do not expand the investigation beyond the request"],
  "handoff": "Return the fact file, source summary, check record, and unresolved claims"
}
```

Owner names record responsibility, not authenticated identity. Write scopes coordinate work, not filesystem access. Distinct local paths can still refer to a shared database, external service, or hidden resource; the coordinator must recognize those conflicts separately.

## Dependencies and parallel work

Ask which actual result each output consumes. That is a dependency. Do not make everything depend on a large planning document, and do not finalize integration while upstream inputs are still unreviewed.

Three independent source sets can be extracted in parallel. Synthesis depends on all three accepted fact sets. Three contributors editing one report should instead produce separate drafts for one integrator.

Choose concurrency within real host, resource, context, and budget limits. Reuse a running task's actual handle when providing corrections; avoid creating duplicate workers for the same output.

## Verify dispatch and receipt

Retain the real task ID or operation handle returned by a collaboration tool. Follow it through the documented status or wait interface. Sending an assignment is not evidence that execution started.

On receipt, check the task identity, version, executor, accessible artifacts, and actual verification. A received file cannot extend permission beyond the current task.

If collaboration is unavailable, execute the same card yourself or wait for a genuinely necessary capability. Do not substitute fictional agent names or fabricated call records.

## Precise rework

A useful correction identifies an unmet condition and a checkable repair:

> Fact 7 turns an estimate in source B into a certain value. Retain the estimate qualifier and keep source A's conflicting value separate. Recheck all numeric facts for a source and certainty label, then return the new artifact and check record.

An instruction to make everything more rigorous is not enough. Expand verification when a correction changes a shared input or contract, and invalidate affected downstream acceptance.

## Time and cost

Honor explicit user budgets and deadlines. When the requested outcome will not fit, preserve completed work and show the concrete remaining gap or smaller viable deliverable. Do not silently overspend.

When no budget is given, inexpensive inspection can establish the work needed. Do not introduce paid providers, subscriptions, or long cloud runs merely to orchestrate. Use actual visible usage and pricing for cost reports; label estimates and their basis rather than inventing exact costs.

## Size a task for the next handoff

Split at an observable output or a meaningful authority boundary, not at every tool call. A task that only says "investigate" needs a concrete deliverable, such as a source-linked cause table with one reproducible failure. A task that bundles investigation, implementation, deployment, and external notification may need separate acceptance and authority checks.

Before dispatch, send only:

1. The intended output and its exact destination or resource.
2. The relevant input references and accepted versions.
3. The acceptance check and evidence expected back.
4. The write scope, protected work, and actual stopping condition.
5. The available budget and the condition that requires escalation.

The executor should return facts and artifacts rather than an expanded transcript. Retain enough raw output at a retrievable location to support the result. If it cannot complete the card, require the observed failure, partial artifact, and one concrete missing condition.

## Integrate results without losing disagreements

Check that each submission used the same accepted interface and input revision. If two outputs conflict, locate the conflicting claim or interface, determine which evidence resolves it, and return a precise rework request. Do not average incompatible facts or treat the most confident executor as the authority.

Use one integration owner for shared output. Review the integrated artifact against the user's acceptance conditions, including interactions that individually passing parts do not exercise. An accepted extraction plus an accepted draft does not prove that the final export or destination is correct.

If a new user correction changes the contract, record it before more dispatch. Reuse unaffected work, invalidate affected consumers, and explain any resulting budget or delivery change. A new instruction should not silently erase a prior failure or authorize an unrelated external action.

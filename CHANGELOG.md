# Changelog

## 1.2.1 — 2026-10-23

- Add bilingual onboarding to repository and standalone copies.
- Bind local example imagery and release documentation to the current version.
- Keep translated Markdown while retaining publication checks for code, paths, and links.

## 1.2.0 — 2026-10-19

- Add explicit orchestration decisions for feasibility, pattern selection, required-work prioritization, integration, and final delivery.
- Add an opt-in MOA command driver with proposal, optional cross-review, synthesis, and repeated-verification stages; explicit criterion coverage, concurrency, call/round budgets, timeouts, and bounded streams.
- Add correction feedback and failed-candidate digest tracking. Unchanged or oscillating failed versions stop with `NO_PROGRESS` instead of retrying until a favorable check.
- Add verifier-only rechecks of accepted candidates and read-only audits of source/artifact hashes, actual stage receipts, criterion coverage, and every required repetition.
- Checkpoint actual process IDs, arguments, exit codes, timing, and request/stdout/stderr evidence. Stop owned POSIX process groups on timeout or output overflow.
- Rank ready board cards by reachable unfinished required work and recommend a disjoint advisory batch through `next --limit`; existing board schema remains version 1.
- Include a runnable offline MOA example with source calculations, cross-review, deliberately failed synthesis, repair, repeated checking, and a separate recheck. It reports zero model calls.
- Add repeatable repository validation with raw logs, actual exit codes, a fixed-source fingerprint, and fail-fast behavior.

The board remains record-only. Model backends, real host-agent integration, meaningful domain checks, and final external delivery remain caller/host responsibilities.

## 1.1.0 — 2026-10-19

- Validate the full accepted ancestor chain before downstream start, submission, acceptance, and resume. Changed ancestor review evidence now blocks those transitions too.
- Add a read-only `next` report for ready work, first blockers, in-flight records, due waits, and stale evidence. It shares start preflight and consumes no attempts.
- Reject malformed current state, incorrectly typed schema versions, missing dependency references, cycles, and accepted states without acceptance evidence. Errors remain structured and preserve the stored payload.
- Prevent installation into the source skill directory, including resolved nested paths, before creating the target.
- Return a structured repository-check failure when core publication files are missing.
- Ship the complete runnable demonstration inside the standalone skill archive; the repository example invokes the same implementation.
- Extend regression coverage and document context handoffs, recovery decisions, readiness snapshots, and compatibility.

Storage remains schema version 1. No model client, external connector, background scheduler, or new execution authority is introduced.

## 1.0.0 — 2026-10-19

Initial public package:

- An English orchestration skill covering goal intake, task dependencies, execution, collaboration, review, waiting, recovery, and delivery.
- A Python-standard-library task board with SQLite transactions and JSON command results.
- Version-pinned local evidence, declared write-scope conflict checks, bounded attempts, and downstream invalidation after reopening work.
- A standalone local demonstration, behavioral tests, and an English documentation set.
- A non-overwriting local skill installer and repository content checks.

Host-specific imports, remote connectors, scheduled execution, and platform coverage are documented separately from local test results. They are not implied by this initial package.

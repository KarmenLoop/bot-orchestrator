# Changelog

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

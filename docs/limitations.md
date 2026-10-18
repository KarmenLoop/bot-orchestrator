# Capabilities and limitations

## Included

The package includes original skill instructions, decision references, a local SQLite task board, an optional executable MOA command driver, behavioral tests, offline examples, installation support, and repeatable repository checks.

The helper supports explicit lifecycle changes, local reference hashing, declared write conflicts, bounded starts, waits, downstream invalidation, and goal closure checks.

## Not included

- A desktop application, web dashboard, or hosted control plane.
- Model inference or API account provisioning.
- Automatic host-agent creation or message sending. The optional MOA driver explicitly executes declared local command adapters and performs bounded local process cleanup; the board itself remains record-only.
- Timers, background daemons, event subscriptions, or automatic wake-ups.
- An OS sandbox, authenticated task principals, or a policy engine.
- Multi-device synchronization or distributed execution leases.
- Automatic verification of a document's truth, a code change's behavior, or an external receipt.

## MOA execution boundary

The command driver is synchronous and opt-in. It invokes caller-supplied argument lists with inherited permissions, accounts, and environment. Per-call working directories organize cooperative adapters; they do not isolate hostile programs. Model clients and real host-agent interfaces are supplied by the caller.

Every declared acceptance criterion needs verifier coverage, and every configured repetition must pass on the same candidate. These are mechanical checks on actual adapter receipts; they do not prove that an always-true verifier or an incorrect criterion is meaningful. Role labels and process IDs do not prove independent models or reviewers.

The driver records timeouts and terminates its owned POSIX process group. Detached descendants, remote operations, and native Windows supervision require host-level handling. A command timeout does not establish whether a remote effect happened. Run deadlines bound adapter work; hashing, recording, and bounded cleanup add local overhead.

Run and recheck directories remain separate. A failed later recheck requires coordinator review and possible board invalidation; later successful runs do not erase it. No global registry silently picks the best result.

## State is not authority

Owner/reviewer labels are not identities. Write declarations are not file permissions. Accepted evidence can be incorrect even when its hash matches. A recorded cancellation does not stop a process, and a due time does not schedule one.

The coordinator must use actual host tools, current authorization, meaningful verification, and reliable external receipts for these responsibilities.

## Local reference boundaries

Evidence must be a regular local file no larger than 64 MiB and resolve within the workspace. The helper rejects ordinary traversal and symlink escapes. This validation is not a hardened sandbox against hostile concurrent filesystem mutation. Use host-native isolation when untrusted local actors can alter paths during execution.

The board is intended for bounded operational goals, not large-scale log storage. It keeps a serialized board record and event history. Use an existing appropriate task store when the workload requires distributed concurrency, high-volume indexing, access-control enforcement, or transactional integration with another product.

## Platform and host acceptance

The helper uses portable Python APIs, with a POSIX-specific FIFO test skipped on platforms without that primitive. Only observed environments should be reported as verified. See [validation](validation.md) for the actual baseline.

A standard skill directory does not prove native import into every host. Loading the text does not prove that an external connector, background task, or account action works.

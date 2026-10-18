# Capabilities and limitations

## Included

The package includes original skill instructions, linked operating references, a local SQLite task board, behavioral tests, a local demonstration, installation support, and repository checks.

The helper supports explicit lifecycle changes, local reference hashing, declared write conflicts, bounded starts, waits, downstream invalidation, and goal closure checks.

## Not included

- A desktop application, web dashboard, or hosted control plane.
- Model inference or API account provisioning.
- Real worker creation, shell execution, process cancellation, or message sending.
- Timers, background daemons, event subscriptions, or automatic wake-ups.
- An OS sandbox, authenticated task principals, or a policy engine.
- Multi-device synchronization or distributed execution leases.
- Automatic verification of a document's truth, a code change's behavior, or an external receipt.

## State is not authority

Owner/reviewer labels are not identities. Write declarations are not file permissions. Accepted evidence can be incorrect even when its hash matches. A recorded cancellation does not stop a process, and a due time does not schedule one.

The coordinator must use actual host tools, current authorization, meaningful verification, and reliable external receipts for these responsibilities.

## Local reference boundaries

Evidence must be a regular local file no larger than 64 MiB and resolve within the workspace. The helper rejects ordinary traversal and symlink escapes. This validation is not a hardened sandbox against hostile concurrent filesystem mutation. Use host-native isolation when untrusted local actors can alter paths during execution.

The board is intended for bounded operational goals, not large-scale log storage. It keeps a serialized board record and event history. Use an existing appropriate task store when the workload requires distributed concurrency, high-volume indexing, access-control enforcement, or transactional integration with another product.

## Platform and host acceptance

The helper uses portable Python APIs, with a POSIX-specific FIFO test skipped on platforms without that primitive. Only observed environments should be reported as verified. See [validation](validation.md) for the actual baseline.

A standard skill directory does not prove native import into every host. Loading the text does not prove that an external connector, background task, or account action works.

# Documentation

Bot Orchestrator combines an agent-facing workflow skill with a local, non-executing task board. Start with the smallest guide that matches your situation.

## First run

1. Follow [installation](installation.md).
2. Run the repository's local demonstration.
3. Read the [skill entry point](../skills/bot-orchestrator/SKILL.md) before using it for a real goal.
4. Use the [board reference](../skills/bot-orchestrator/references/board.md) only when persistent local records are useful.

## Working guides

- [Architecture](architecture.md): coordinator, host, board, artifacts, and lifecycle.
- [Execution](../skills/bot-orchestrator/references/execution.md): task cards, ownership, dependencies, collaboration, and review.
- [Capabilities](../skills/bot-orchestrator/references/capabilities.md): real tools, external actions, and scheduling boundaries.
- [Recovery](../skills/bot-orchestrator/references/recovery.md): checkpoints, uncertain effects, invalidation, pause, and resume.
- [Board commands](../skills/bot-orchestrator/references/board.md): initialization through goal closure.
- [Examples](../skills/bot-orchestrator/references/examples.md): local walkthrough and realistic branches.

## Verification and maintenance

- [Validation](validation.md)
- [Limitations](limitations.md)
- [Troubleshooting](troubleshooting.md)
- [Release process](releasing.md)
- [Contributing](../CONTRIBUTING.md)
- [Security](../SECURITY.md)
- [Support](../SUPPORT.md)

The helper's tests establish local behavior. Host discovery, model behavior, external connections, and future wake-ups need separate evidence in the environment where they are used.

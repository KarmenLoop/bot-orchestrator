# Security

## Reporting a vulnerability

If GitHub private vulnerability reporting is enabled for this repository, use **Security → Report a vulnerability**. If it is unavailable, open a public issue containing only a request for a private reporting channel. Do not include exploit payloads, credentials, private files, or sensitive database content in that public request.

No private reporting feature or response-time commitment is assumed merely because this file exists. Do not send sensitive information until a maintainer provides a suitable channel.

## Trust boundaries

- The local board stores planning and evidence metadata. It is not an operating-system sandbox or an identity authority.
- Declared write scopes coordinate tasks; they do not prevent unrelated processes from writing files.
- Owner and reviewer names are labels, not authenticated principals.
- Evidence hashes detect changes to referenced local files. They do not prove correctness, provenance, honest logs, or the outcome of an external operation.
- A `running` or `cancelled` record does not start or stop a real process.
- A reminder timestamp does not create a scheduled job.
- The skill does not grant permission to use accounts, send messages, spend money, publish content, or change operating-system permissions.

The optional MOA driver executes declared commands with inherited host permissions and environment. Inspect specs before execution, keep secrets out of argv and captured outputs, and use synchronous bounded adapters. Owned POSIX process-group cleanup does not cancel remote effects or supervise detached services.

Use host-native isolation, account protection, approval controls, and execution limits where required.

## Safe reproductions

Prefer a small synthetic workspace and the included tests. Do not publish a live SQLite board or artifact set without reviewing it for personal information, secrets, internal paths, and confidential content.

## Supported versions

Report the exact version or commit. Maintainers will assess reports against the latest published source. No long-term support window is promised.

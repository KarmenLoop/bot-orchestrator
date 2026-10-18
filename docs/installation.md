# Installation

## Requirements

- Python 3.9 or newer for the optional board, installer, tests, and local example.
- A host that can load the skill's Markdown instructions for agent-guided use.
- The host's actual tools and permissions for the work you intend to perform.

No model key or network service is needed to run the local example. The Python tools use only the standard library.

## Obtain the repository

```bash
git clone https://github.com/KarmenLoop/bot-orchestrator.git
cd bot-orchestrator
python3 examples/local_demo.py
```

For a standalone release archive, extract it and run `python3 scripts/demo.py` from the skill directory. Alternatively, extract a complete repository ZIP downloaded through GitHub's Code menu. The demonstration writes to a new temporary directory and prints its location.

## Codex

```bash
python3 scripts/install_skill.py
```

The default location is `$CODEX_HOME/skills/bot-orchestrator`, falling back to `~/.codex/skills/bot-orchestrator` when `CODEX_HOME` is unset. Existing destinations are never overwritten. A destination inside the source skill directory is also rejected before creating directories, preventing recursive self-copy.

An explicit destination is also supported:

```bash
python3 scripts/install_skill.py --destination /absolute/path/to/skills/bot-orchestrator
```

Restart the host session or refresh its skill discovery according to its documented behavior. Use `$bot-orchestrator` where that invocation syntax is supported. Listing a skill proves discovery, not successful access to every external tool it may discuss.

## Other hosts

Copy the entire `skills/bot-orchestrator` directory, including its references, scripts, metadata, and license, to the host's documented skill location. Do not copy only `SKILL.md` and leave its references behind.

Import formats and invocation syntax differ. If a host cannot load companion files, adapt the package through that host's documented process and validate the actual result. Native import into a particular bot product is not claimed solely from this package's structure.

## Upgrade

The installer intentionally has no force-overwrite option. Inspect the new version, back up or rename the existing skill directory, then install into the intended destination. Preserve any user-specific adaptation and keep task databases outside the skill directory.

Do not replace a live task board by copying a fresh sample over it. Schema changes require a separately designed migration; an unsupported schema must remain rejected.

## Remove

Remove only the skill directory that you installed. This does not cancel external work, revoke account sessions, or delete task workspaces. Settle those through the corresponding host tools and retain or remove artifacts according to the user's actual request.

## Windows

Use `python` or `py -3` if `python3` is not the available command. Commands use subprocess argument lists rather than a shell. The helper is designed around portable Python and SQLite, but platform-specific behavior must be checked on the target environment. See [validation](validation.md).

# Bot Orchestrator: from download to a checked handoff

English | [简体中文](tutorial.zh-CN.md) · [Project](../README.md)

This guide matches **v1.2.1**.

## 1. Download and verify

Download the complete bot-orchestrator-v1.2.1.zip and SHA256SUMS.txt, or choose the smaller skill ZIP for host installation. Compare the full hash with shasum -a 256 on macOS, sha256sum on Linux, or Get-FileHash -Algorithm SHA256 in PowerShell before extracting. Python 3.9+ and its standard library are sufficient; no pip dependencies are required. On Windows replace python3 with py -3.

## 2. Run and inspect the first job

```sh
python3 scripts/demo.py
```

Expect ok: true, goalStatus: done, and facts.json, summary.md, board.sqlite3 in the artifact list. Open the printed workspace and check the two amounts and total 42. This is a local self-review, not independent acceptance.

Inside a standalone skill, run scripts/demo.py instead. The demo creates a temporary workspace and retains its artifacts; remove only that demo’s directory after inspection if no longer needed.

## 3. Install and configure

```sh
python3 scripts/board.py --help
```

The target must be a new directory outside the source. Load the complete folder through a host-supported skill path and confirm SKILL.md and references are readable. The host supplies accounts, models, tools, and authorization; the board itself needs no API key. Choose an explicit database and workspace for each job.

## 4. Create your own board

Replace these example paths with your own absolute paths:

```sh
python3 scripts/board.py --db /path/to/job/board.sqlite3 init --workspace /path/to/job --goal "Prepare an expense summary" --acceptance "Values match the source and total 42"
python3 scripts/board.py --db /path/to/job/board.sqlite3 add facts --objective "Record amounts 17 and 25" --check "Both values retained; total is 42" --deliverable facts.json
python3 scripts/board.py --db /path/to/job/board.sqlite3 next
```

Inside an installed skill, use scripts/board.py. Start facts, perform the work, and write a real check file. Submit with submit facts --evidence CHECK_FILE --note NOTE. Review with review facts --decision accept or rework, supplying --evidence and --reason. Quote arguments that contain spaces. The complete board reference is references/board.md inside the skill.

## 5. Practice evidence changes, waiting, and repair

Use status --full to read stored state and verify to check evidence. Change an accepted deliverable and observe verify’s nonzero result; an earlier acceptance no longer establishes unchanged bytes. Reopen invalidates dependent acceptance. Waiting, blocked, and cancelled marks need a reason; resuming requires checking the real condition again.

```sh
python3 scripts/moa_demo.py
```

The MOA demo checks a candidate, finds an error, repairs it, and rechecks. It uses local adapters and no model requests. Before configuring a real adapter, verify its invocation contract, authorization, budget, timeout, replay rules, and actual receipts. A passing demo does not establish a connected host or provider.

## 6. Troubleshoot and validate

Exit codes are 0 for command success, 1 when verify detects changed evidence, and 2 for invalid input, lifecycle, conflict, or I/O problems. Inspect an existing installation instead of forcing replacement. If discovery fails, check the host’s skill root and refresh it. Verify uncertain external sends before considering a retry.

```sh
python3 -B scripts/test_board.py
python3 -B scripts/test_moa.py
python3 -B scripts/demo.py
```

## 7. Update, roll back, and uninstall

Finish active writes and back up the skill and task database separately. Verify a new version, install into a new directory, and switch deliberately. Retain the old skill for rollback and preserve newer task facts. Removing a folder does not unregister a schedule created separately in a host; cancel and confirm it there. Uninstall only the inspected skill path, retaining workspace data.

[MIT](../LICENSE) · [NOTICE](../NOTICE)

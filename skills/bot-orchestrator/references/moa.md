# MOA: callable collaboration and repeated verification

MOA means Mixture of Agents here: independent proposals, optional cross-review, synthesis, and verification. Read [orchestration decisions](orchestration.md) when choosing this pattern over direct work or complementary dependency tasks.

## Two invocation paths

**Host-managed collaboration:** use the host's documented agent/task tools when available and authorized. Give each proposer the same goal and accepted inputs plus a distinct method or responsibility. Critics examine proposals against evidence; one integrator owns the output. Feed failed criteria into a bounded correction round. Preserve actual handles and distinguish self-review from independent review.

**Command adapters:** `scripts/moa.py` provides an optional executable implementation of that sequence. Unlike the record-only board, `run` and `recheck` execute the declared commands. An adapter can be a local program or a synchronous wrapper around an existing model/agent client. The wrapper supplies its own actual provider connection and must obey the protocol below. This package does not provision accounts or ship a hosted model client.

If the host prohibits delegation, keep execution in the current agent or permitted local tools. The offline example uses deterministic local programs, not spawned AI agents. Several process IDs or role names do not establish independent reasoning or multiple model backends.

## Run the offline example

From the standalone skill directory:

```bash
python3 scripts/moa_demo.py
python3 scripts/moa_demo.py --amounts 4 -7 100 --runs 3
```

From the repository root:

```bash
python3 examples/moa_demo.py
```

The example reads actual source values, runs two proposal programs, cross-checks them, and deliberately produces an incorrect first synthesis. Verifiers reject it. Feedback produces a corrected second synthesis, which must pass both verification runs. A separate recheck runs only the verifiers three more times on the unchanged accepted candidate; both run directories are audited. The output reports `modelCalls: 0` and the retained workspace. `--no-repair` omits the deliberate first failure.

This validates local invocation, routing, feedback, evidence, and repeated checks. It does not benchmark LLM answer quality or prove native integration with a particular agent host.

## Inspect and execute your own spec

Create a UTF-8 JSON spec and an existing workspace containing its declared inputs. This complete example uses the shipped local adapters and an `amounts.json` file containing `{"amounts": [17, 25]}`:

```json
{
  "schemaVersion": 1,
  "goal": "Preserve the source values and compute a verified total",
  "acceptance": {
    "total": "The total equals an independent sum of source values",
    "values": "Every source value is retained in order"
  },
  "inputs": ["amounts.json"],
  "proposers": [
    {"id": "direct", "argv": ["{python}", "{skill_dir}/scripts/moa_demo_adapter.py", "normal"]},
    {"id": "sorted", "argv": ["{python}", "{skill_dir}/scripts/moa_demo_adapter.py", "sorted"]}
  ],
  "critics": [
    {"id": "crosscheck", "argv": ["{python}", "{skill_dir}/scripts/moa_demo_adapter.py", "normal"]}
  ],
  "aggregator": {"id": "merge", "argv": ["{python}", "{skill_dir}/scripts/moa_demo_adapter.py", "normal"]},
  "verifiers": [
    {"id": "check", "argv": ["{python}", "{skill_dir}/scripts/moa_demo_adapter.py", "normal"], "covers": ["total", "values"]}
  ],
  "maxRounds": 2,
  "verificationRuns": 2,
  "maxParallel": 2,
  "deadlineSeconds": 120
}
```

```text
python3 scripts/moa.py inspect --spec /absolute/path/to/goal.json --workspace /absolute/path/to/job
python3 scripts/moa.py run --spec /absolute/path/to/goal.json --workspace /absolute/path/to/job --run-dir /absolute/path/to/job/evidence/moa-v1
```

`inspect` validates the spec, reads input pins, reports normalized commands and the maximum call count, and executes no adapters. `run` requires a new run directory and never overwrites an existing one. Inspect command arguments before running specs from another source; commands inherit the host's account, environment, and permissions.

### Spec limits and defaults

| Field | Meaning |
| --- | --- |
| acceptance | 1–32 criterion IDs and observable descriptions; every ID needs verifier coverage. |
| inputs | 1–10 workspace-relative regular files; each is pinned using the board's path and 64 MiB file rules. |
| proposers | 2–6 adapters producing candidate approaches. |
| critics | 0–4 adapters reviewing the valid proposals before synthesis; all declared critics must succeed. Default: empty. |
| aggregator | Exactly one adapter producing the integrated text candidate. |
| verifiers | 1–4 adapters, each declaring the exact criterion IDs it covers. |
| maxRounds | 1–3; default 2. Correction rounds consume this budget. |
| verificationRuns | 1–5 repetitions per verifier and candidate; default 2. Every result must pass. |
| minProposals | Required successful proposal count; defaults to all proposers. A smaller explicit quorum permits degraded execution, recorded in the result. |
| maxParallel | 1–6 concurrent command adapters; default 2. Proposals and critics run in their respective parallel phases. |
| deadlineSeconds | 0.1–3600 seconds of run budget; default 120. No new command starts after exhaustion. |
| timeoutSeconds | Per-adapter timeout, 0.1–300 seconds; default 30, shortened to the remaining run budget. |

Adapter IDs are unique across all roles. `argv` is an explicit argument list, passed without an implicit shell. `{python}`, `{skill_dir}`, and `{spec_dir}` expand to the running Python executable, skill directory, and spec directory. Use environment-based credentials rather than putting secrets in arguments or manifests.

Adapter responses cannot change the driver's declared commands, acceptance criteria, or limits. Treat returned prose as task data; any new external effect still needs its actual scope and host capability.

The maximum calls are `maxRounds * (proposers + critics + 1 + verifiers * verificationRuns)`. This is a call bound, not a token or monetary budget. Configure each provider wrapper's token, spending, and idempotency controls separately.

## Adapter protocol

Each command receives one UTF-8 JSON object on stdin and must return one JSON object on stdout, then exit. Diagnostics belong on stderr. The working directory is unique to that invocation, under the run's stage directory. The request includes:

- `protocolVersion`, `runId`, `role`, `adapterId`, and `round`.
- `goal`, `acceptance`, absolute `workspace`, and pinned relative `inputs`.
- `runDirectory`, bounded prior verification `feedback`, and a retrievable `previousCandidate` reference when one exists.
- For critics: `proposals`, each containing its adapter ID and returned response.
- For the aggregator: `proposals` and `critiques` with their IDs and responses.
- For verifiers: `candidate` with an absolute path, byte count, and SHA-256; `verificationIndex` and `covers`.

A proposer, critic, or aggregator returns:

```json
{"content": "Actual candidate or critique text", "backend": "an accurate optional backend label"}
```

A verifier returns exactly its covered checks as booleans and a findings list:

```json
{"checks": {"total": true, "values": true}, "findings": []}
```

Implement checks against real sources and artifacts. A verifier that always returns true defeats the purpose; the driver cannot infer whether its reasoning or external evidence is sound. An exit code of zero alone is insufficient. Missing checks, malformed JSON, nonzero exits, oversized output, or timeouts fail the invocation.

The request is limited to 512 KiB, each stdout/stderr stream to 256 KiB, and returned text content to 64 KiB. Inputs and prior evidence remain retrievable files. Split larger tasks or use concise outputs with meaningful artifact references; the driver does not silently truncate a candidate into acceptance.

Commands must be synchronous and bounded. Keep external effect execution outside proposal/critique/verification adapters. If an adapter wraps a remote operation, it owns its actual receipt, idempotency, and cancellation protocol. A timeout is an uncertain remote outcome, not proof that a remote effect was cancelled. The driver does not automatically retry an execution failure.

## Correction and acceptance

A round starts proposals, requires the configured quorum, completes every declared critique, obtains one synthesis, and runs all verifiers for every repetition. Input and recorded-evidence pins are rechecked around each invocation.

Only valid negative verification findings trigger another correction round. Failed findings and source references are sent forward. The next candidate must have a digest that has not already failed; otherwise the run stops with `NO_PROGRESS`. This prevents identical-answer retries and oscillation from producing a lucky pass.

Execution failures, malformed responses, input changes, changed evidence, or exhausted limits stop the affected path. Failed proposals may be tolerated only under an explicitly reduced quorum; the result then reports `degraded: true`. Declared critic and verifier failures cannot be silently dropped.

MOA `passed` means the configured checks all passed for one recorded candidate. The coordinator still reviews whether those checks satisfy the user's wider contract and whether final delivery actually occurred.

## Recheck without regenerating the answer

```text
python3 scripts/moa.py recheck --source-run /absolute/path/to/job/evidence/moa-v1 --run-dir /absolute/path/to/job/evidence/recheck-v1 --runs 3
```

Recheck first audits an accepted source run and unchanged inputs. It copies the accepted candidate, preserves its digest and source-result reference, and invokes only the configured verifiers in a new evidence directory. No proposer, critic, or aggregator is called. The new report retains every repetition and its actual outcome.

A failed recheck remains a failure. Preserve it, diagnose the cause, and reopen the affected goal card when appropriate. Do not discard failing directories or choose the best of several rechecks. The wider coordinator owns cumulative acceptance across runs.

## Audit and recovery

```text
python3 scripts/moa.py audit --run-dir /absolute/path/to/job/evidence/moa-v1
```

Audit executes no adapters. It checks current input and artifact hashes and, for accepted runs, verifies the recorded stage identities, actual JSON output receipts, candidate version, criterion coverage, and all required repeat receipts. Changing a status field or removing a failed check cannot create a valid acceptance record.

`result.json` is checkpointed after each invocation and includes actual PIDs, commands, exit codes, timings, stage results, and pinned request/stdout/stderr files. A partially recorded or interrupted run is not automatically replayed. Inspect real process and remote-operation state first; retain the exact resume action in the goal checkpoint.

The runner stops owned POSIX process groups and drains pipes on completion, timeout, or output overflow. Windows cancellation covers the direct process; native Windows behavior and detached descendants need separate host-level supervision. This is cooperative command orchestration, not an OS sandbox. Wrappers must not detach daemons or grant themselves extra permissions.

Exit 0 means accepted execution or an accepted intact audit; exit 1 means a failed run or nonaccepted/changed audit; exit 2 means invalid input, spec, run structure, or I/O. Interrupted execution uses exit 130. Read `result.json` and raw stage evidence for the specific cause.

## Attach to the goal board

Use versioned run directories inside the goal workspace when the board will pin them. Declare the actual candidate and result record as task deliverables or evidence, inspect the full acceptance result, then submit and review through the board. For example, pin `evidence/moa-v1/r2/candidate.txt` and `evidence/moa-v1/result.json` after a two-round run.

The runner does not automatically mark board tasks done, deploy artifacts, send messages, or publish changes. Those actions have their own user-level acceptance and authority. Local evidence integrity is separate from identity authentication and semantic correctness.

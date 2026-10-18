# Worked scenarios

## Local demonstration

The public repository includes examples/local_demo.py. From the repository root, run:

```bash
python3 examples/local_demo.py
```

It creates a temporary workspace, generates a fact file containing 17 and 25, verifies the total 42, submits and reviews the facts, generates and reviews a consistent summary, verifies the file references, and closes the goal. It prints the workspace path. It does not use a model, network service, external account, or existing project.

For a standalone skill installation without the repository examples directory, follow the board commands in board.md using your own synthetic inputs. The board remains a record: the host or operator must perform the actual work and checks.

## Research with missing information

A user asks for an application packet from supplied materials, with missing facts flagged for later completion.

Extract confirmed facts and a gap list. Draft the sections the available evidence supports; do not stop all work because one field is missing. Preserve unknown fields rather than inventing numbers, history, or credentials.

Record an explicit wait for the required information. Do not create a recurring reminder unless the user requested future follow-up. When information arrives, match it to the existing gap and resume the same goal, preserving already-accepted work.

If the user later requests external submission, check the actual authorization, recipient, and attachments. A completed local packet is not evidence of an external submission.

## Uncertain external effects

A user authorized sending an agreed file to a specified recipient. The tool times out after the request was sent.

Retain the original operation ID, target, attachment digest, and timeout observation. Inspect the operation or sent-item history before retrying. If no reliable query or idempotency mechanism exists, report the uncertainty and duplicate-send risk rather than quietly sending again through another account or channel.

## A host without delegation

A user needs an analysis report, but the host prohibits workers.

Use task cards for source checks, analysis, drafting, and review, and execute them sequentially with owner current-agent. Report self-review honestly. Do not invent a researcher, engineer, and reviewer who never existed.

## Changed upstream evidence

The board says the fact table and report are done, but verify detects a different fact-file digest.

Inspect the change. For a legitimate new input, reopen the extraction task, retain the old report, and block affected acceptance. Review the new facts before updating the report. If the reference should have been an immutable historical version, locate and inspect that version; do not simply replace its digest to make the board appear clean.

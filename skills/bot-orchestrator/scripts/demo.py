#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run a real local board workflow using only a disposable workspace."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    workspace = Path(tempfile.mkdtemp(prefix='bot-orchestrator-demo-'))
    script = Path(__file__).with_name('board.py')
    base = [sys.executable, str(script), '--db', str(workspace / 'board.sqlite3')]

    def board(*args):
        result = subprocess.run(base + list(args), check=True, capture_output=True, text=True, timeout=15)
        return json.loads(result.stdout)

    def save(name, text):
        (workspace / name).write_text(text, encoding='utf-8')

    board('init', '--workspace', str(workspace), '--goal', 'Deliver a checked expense summary',
          '--acceptance', 'Preserve both source values, verify total 42, and check the summary')
    board('add', 'facts', '--objective', 'Record source facts', '--check', 'Values 17 and 25 sum to 42',
          '--deliverable', 'facts.json')
    board('add', 'summary', '--objective', 'Write a consistent summary', '--check', 'Summary agrees with accepted facts',
          '--deliverable', 'summary.md', '--depends', 'facts')
    board('start', 'facts')
    facts = {'amounts': [17, 25], 'total': 17 + 25}
    save('facts.json', json.dumps(facts))
    assert json.loads((workspace / 'facts.json').read_text())['total'] == 42
    save('facts-check.txt', 'PASS: 17 + 25 == 42; facts.json read back.')
    board('submit', 'facts', '--evidence', 'facts-check.txt', '--note', 'Facts generated and checked')
    save('facts-review.txt', 'SELF REVIEW: Both input values retained; total recomputed as 42.')
    board('review', 'facts', '--decision', 'accept', '--evidence', 'facts-review.txt', '--reason', 'Fact checks passed')
    board('start', 'summary')
    readback = json.loads((workspace / 'facts.json').read_text())
    save('summary.md', 'The two expenses are 17 and 25, for a total of 42.\n')
    assert str(readback['total']) in (workspace / 'summary.md').read_text()
    save('summary-check.txt', 'PASS: Summary values match accepted source facts.')
    board('submit', 'summary', '--evidence', 'summary-check.txt', '--note', 'Summary generated and checked')
    save('summary-review.txt', 'SELF REVIEW: Both amounts and the total match; no additional facts introduced.')
    board('review', 'summary', '--decision', 'accept', '--evidence', 'summary-review.txt', '--reason', 'Summary checks passed')
    assert board('verify')['ok']
    save('final-check.txt', 'PASS: Both files readable; values and total agree.')
    board('close', '--evidence', 'final-check.txt', '--reason', 'User-level checks passed')
    assert board('status')['status'] == 'done'
    print(json.dumps({'ok': True, 'workspace': str(workspace), 'goalStatus': 'done',
                      'artifacts': ['facts.json', 'summary.md', 'board.sqlite3']}, indent=2))


if __name__ == '__main__':
    main()

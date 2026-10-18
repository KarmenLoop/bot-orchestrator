#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Deterministic process adapter for offline MOA protocol checks; no model calls."""
import json
from pathlib import Path
import sys
import subprocess
import time


def main():
    request = json.load(sys.stdin)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'normal'
    if mode == 'crash':
        print('intentional adapter failure', file=sys.stderr)
        return 7
    if mode == 'invalid':
        print('not a JSON response')
        return 0
    if mode == 'descendant':
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        Path('child.pid').write_text(str(child.pid))
        time.sleep(30)
    if mode == 'sleep':
        time.sleep(3)
    if mode == 'flood':
        print('x' * (300 * 1024))
        return 0
    source = Path(request['workspace']) / request['inputs'][0]['path']
    amounts = json.loads(source.read_text(encoding='utf-8'))['amounts']
    role = request['role']
    if role == 'propose':
        # Different calculation orders exercise separate real process calls.
        values = sorted(amounts) if mode == 'sorted' else amounts
        response = {'content': json.dumps({'amounts': amounts, 'total': sum(values) + (1 if mode == 'wrong' else 0)}),
                    'backend': 'deterministic-demo'}
    elif role == 'critique':
        invalid = [p['id'] for p in request['proposals'] if
                   json.loads(p['response']['content']).get('total') != sum(amounts)]
        response = {'content': json.dumps({'invalidCandidateIds': invalid}), 'backend': 'deterministic-demo'}
    elif role == 'aggregate':
        invalid = {key for c in request.get('critiques', []) for key in json.loads(c['response']['content'])['invalidCandidateIds']}
        request['proposals'] = [p for p in request['proposals'] if p['id'] not in invalid]
        candidates = [json.loads(p['response']['content']) for p in request['proposals']]
        answer = candidates[0]
        if mode == 'repair' and not request['feedback']:
            answer['total'] += 1  # Deliberate failing first draft for the recovery example.
        elif mode == 'always-wrong':
            answer['total'] += 1
        response = {'content': json.dumps(answer), 'backend': 'deterministic-demo'}
    else:
        candidate = Path(request['candidate']['path'])
        answer = json.loads(candidate.read_text(encoding='utf-8'))
        checks = {'total': answer.get('total') == sum(amounts), 'values': answer.get('amounts') == amounts}
        if mode == 'first-round-fails' and request['round'] == 1:
            checks['total'] = False
        if mode == 'flaky' and request['verificationIndex'] == 2:
            checks['total'] = False
        if mode == 'missing-check':
            checks.pop('total')
        if mode == 'mutate':
            candidate.write_text('changed by verifier', encoding='utf-8')
        if mode == 'change-input':
            source.write_text(json.dumps({'amounts': [999]}), encoding='utf-8')
        response = {'checks': checks, 'findings': [key + ' mismatched' for key, value in checks.items() if not value],
                    'backend': 'deterministic-demo'}
    print(json.dumps(response))
    return 0


if __name__ == '__main__':
    sys.exit(main())

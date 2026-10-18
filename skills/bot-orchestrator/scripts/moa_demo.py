#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise real MOA process orchestration offline, including repair and recheck."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--amounts', type=int, nargs='+', default=[17, 25])
    parser.add_argument('--runs', type=int, choices=range(1, 6), default=3)
    parser.add_argument('--no-repair', action='store_true', help='Omit the deliberately failing first draft.')
    args = parser.parse_args()
    root = Path(tempfile.mkdtemp(prefix='bot-moa-demo-'))
    (root / 'amounts.json').write_text(json.dumps({'amounts': args.amounts}), encoding='utf-8')

    def adapter(key, mode='normal'):
        return {'id': key, 'argv': ['{python}', '{skill_dir}/scripts/moa_demo_adapter.py', mode], 'timeoutSeconds': 5}

    spec = {'schemaVersion': 1, 'goal': 'Produce a checked summary from source amounts',
            'acceptance': {'total': 'The total equals an independent sum of source values',
                           'values': 'Every source value is retained in order'},
            'inputs': ['amounts.json'], 'proposers': [adapter('direct'), adapter('sorted', 'sorted')],
            'critics': [adapter('crosscheck')],
            'aggregator': adapter('merge', 'normal' if args.no_repair else 'repair'),
            'verifiers': [dict(adapter('check'), covers=['total', 'values'])],
            'maxRounds': 2, 'verificationRuns': 2, 'maxParallel': 2, 'deadlineSeconds': 30}
    path = root / 'spec.json'; path.write_text(json.dumps(spec, indent=2), encoding='utf-8')
    script = Path(__file__).with_name('moa.py')

    def invoke(*arguments):
        result = subprocess.run([sys.executable, '-B', str(script), *map(str, arguments)],
                                check=True, capture_output=True, text=True, timeout=45)
        return json.loads(result.stdout)

    preflight = invoke('inspect', '--spec', path, '--workspace', root)
    initial = invoke('run', '--spec', path, '--workspace', root, '--run-dir', root / 'initial')
    repeated = invoke('recheck', '--source-run', root / 'initial', '--run-dir', root / 'recheck', '--runs', args.runs)
    assert invoke('audit', '--run-dir', root / 'initial')['ok']
    assert invoke('audit', '--run-dir', root / 'recheck')['ok']
    value = json.loads(Path(initial['candidate']).read_text(encoding='utf-8'))
    assert value == {'amounts': args.amounts, 'total': sum(args.amounts)}
    first = json.loads((root / 'initial/result.json').read_text(encoding='utf-8'))
    second = json.loads((root / 'recheck/result.json').read_text(encoding='utf-8'))
    assert first['candidateSha256'] == second['candidateSha256']
    print(json.dumps({'ok': True, 'kind': 'offline-process-demonstration', 'modelCalls': 0,
                      'workspace': str(root), 'total': value['total'], 'initialStatus': initial['status'],
                      'roundResults': [r['passed'] for r in first['rounds']], 'recheckStatus': repeated['status'],
                      'recheckCalls': len(second['calls']), 'candidateSha256': first['candidateSha256'],
                      'maximumInitialCalls': preflight['maximumCalls']}, indent=2))


if __name__ == '__main__':
    main()

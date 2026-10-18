#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Repeat local acceptance checks, preserving every exit code and raw log."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def source_fingerprint():
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts)
    digest = hashlib.sha256()
    for file in files:
        digest.update(file.relative_to(ROOT).as_posix().encode('utf-8') + b'\x00')
        digest.update(hashlib.sha256(file.read_bytes()).digest())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeat', type=int, choices=range(1, 11), default=3)
    parser.add_argument('--output', required=True, type=Path, help='New evidence directory outside this repository.')
    args = parser.parse_args()
    target = args.output.expanduser().resolve()
    if target == ROOT or ROOT in target.parents or target.exists():
        print(json.dumps({'ok': False, 'error': 'Use a new output directory outside the repository.'}))
        return 2
    target.mkdir(parents=True)
    before = source_fingerprint()
    checks = [('board', 'skills/bot-orchestrator/scripts/test_board.py'),
              ('moa', 'skills/bot-orchestrator/scripts/test_moa.py'),
              ('package', 'scripts/test_repository.py'), ('content', 'scripts/check_repository.py'),
              ('board-demo', 'examples/local_demo.py'), ('moa-demo', 'examples/moa_demo.py')]
    report = {'ok': False, 'python': sys.version, 'platform': sys.platform, 'repeat': args.repeat,
              'sourceSha256': before, 'startedAt': dt.datetime.now(dt.timezone.utc).isoformat(), 'checks': []}
    try:
        for iteration in range(1, args.repeat + 1):
            for name, path in checks:
                command = [sys.executable, '-B', path]
                log = target / ('cycle-{}-{}.log'.format(iteration, name))
                started = time.monotonic()
                with log.open('xb') as stream:
                    try:
                        process = subprocess.run(command, cwd=str(ROOT), stdout=stream, stderr=subprocess.STDOUT, timeout=120)
                        code = process.returncode
                    except subprocess.TimeoutExpired:
                        code = 124
                output = log.read_text(encoding='utf-8', errors='replace')
                count = re.search(r'Ran (\d+) tests?', output)
                result = {'cycle': iteration, 'check': name, 'command': command, 'exitCode': code,
                          'durationMs': round((time.monotonic() - started) * 1000), 'log': log.name,
                          'tests': int(count.group(1)) if count else None,
                          'sha256': hashlib.sha256(log.read_bytes()).hexdigest()}
                report['checks'].append(result)
                print(json.dumps(result), flush=True)
                (target / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
                if code:
                    report['failure'] = 'A check failed or timed out; remaining checks were not run.'
                    return 1
        report['sourceUnchanged'] = source_fingerprint() == before
        report['ok'] = report['sourceUnchanged']
        if not report['ok']:
            report['failure'] = 'Source changed during validation; repeat against one fixed revision.'
        return 0 if report['ok'] else 1
    finally:
        report['finishedAt'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (target / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'ok': report['ok'], 'report': str(target / 'report.json')}), flush=True)


if __name__ == '__main__':
    sys.exit(main())

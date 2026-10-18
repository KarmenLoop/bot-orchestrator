#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Opt-in MOA command adapters: inspect, run, recheck, and audit evidence."""
import argparse
import asyncio
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import sys
import time
import uuid

from board import BoardError, changed, now, pin, require

MAX_STREAM = 256 * 1024
MAX_CONTENT = 64 * 1024
MAX_REQUEST = 512 * 1024
MAX_JSON = 16 * 1024 * 1024


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2).encode('utf-8') + b'\n'


def read_json(path):
    require(path.is_file() and stat.S_ISREG(path.stat().st_mode) and path.stat().st_size <= MAX_JSON,
            'INVALID_JSON_FILE', 'Use a bounded regular JSON file.')
    return json.loads(path.read_text(encoding='utf-8'))


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value) is not None


def text(value):
    return isinstance(value, str) and bool(value.strip())


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def seconds(value, high):
    return type(value) in (int, float) and math.isfinite(value) and 0.1 <= value <= high


def validate_spec(value, directory):
    def valid(condition):
        require(condition, 'INVALID_SPEC', 'Invalid MOA spec; inspect field types, IDs, commands, and limits.')
    valid(isinstance(value, dict))
    allowed = {'schemaVersion', 'goal', 'acceptance', 'inputs', 'proposers', 'aggregator', 'verifiers',
               'maxRounds', 'verificationRuns', 'minProposals', 'maxParallel', 'deadlineSeconds', 'critics'}
    valid(not set(value) - allowed and type(value.get('schemaVersion')) is int and value['schemaVersion'] == 1)
    valid(text(value.get('goal')) and len(value['goal'].encode('utf-8')) <= 8192)
    acceptance = value.get('acceptance')
    valid(isinstance(acceptance, dict) and 1 <= len(acceptance) <= 32 and
          all(identifier(k) and text(v) and len(v.encode('utf-8')) <= 2048 for k, v in acceptance.items()))
    valid(isinstance(value.get('inputs'), list) and 1 <= len(value['inputs']) <= 10 and all(text(p) for p in value['inputs']))
    valid(isinstance(value.get('proposers'), list) and 2 <= len(value['proposers']) <= 6)
    valid(isinstance(value.get('verifiers'), list) and 1 <= len(value['verifiers']) <= 4)
    valid(isinstance(value.get('critics', []), list) and len(value.get('critics', [])) <= 4)
    result = dict(value)
    defaults = {'maxRounds': 2, 'verificationRuns': 2, 'minProposals': len(value['proposers']),
                'maxParallel': 2, 'deadlineSeconds': 120}
    for key, default in defaults.items():
        result.setdefault(key, default)
    valid(integer(result['maxRounds'], 1, 3) and integer(result['verificationRuns'], 1, 5) and
          integer(result['minProposals'], 1, len(value['proposers'])) and integer(result['maxParallel'], 1, 6) and
          seconds(result['deadlineSeconds'], 3600))
    identifiers = set()

    def adapter(item, verifier=False):
        valid(isinstance(item, dict) and not set(item) - ({'id', 'argv', 'timeoutSeconds', 'covers'} if verifier else
                                                       {'id', 'argv', 'timeoutSeconds'}))
        valid(identifier(item.get('id')) and item['id'] not in identifiers)
        identifiers.add(item['id'])
        valid(isinstance(item.get('argv'), list) and 1 <= len(item['argv']) <= 64 and
              all(text(a) and '\x00' not in a and len(a.encode('utf-8')) <= 8192 for a in item['argv']))
        timeout = item.get('timeoutSeconds', 30)
        valid(seconds(timeout, 300))
        replacements = {'{python}': sys.executable, '{skill_dir}': str(Path(__file__).resolve().parent.parent),
                        '{spec_dir}': str(directory)}
        argv = []
        for arg in item['argv']:
            for token, replacement in replacements.items():
                arg = arg.replace(token, replacement)
            argv.append(arg)
        entry = dict(item, argv=argv, timeoutSeconds=timeout)
        if verifier:
            valid(isinstance(item.get('covers'), list) and bool(item['covers']) and
                  all(isinstance(c, str) and c in acceptance for c in item['covers']) and
                  len(set(item['covers'])) == len(item['covers']))
        return entry

    result['proposers'] = [adapter(a) for a in value['proposers']]
    result['critics'] = [adapter(a) for a in value.get('critics', [])]
    result['aggregator'] = adapter(value.get('aggregator'))
    result['verifiers'] = [adapter(a, True) for a in value['verifiers']]
    covered = {c for a in result['verifiers'] for c in a['covers']}
    require(covered == set(acceptance), 'UNCOVERED_ACCEPTANCE', 'Every acceptance criterion needs a declared verifier.')
    return result


def source_inputs(spec, workspace):
    require(workspace.is_dir(), 'INVALID_WORKSPACE', 'Workspace must already exist.')
    return [pin(workspace, name) for name in spec['inputs']]


def inspect_spec(spec, inputs):
    per_round = len(spec['proposers']) + len(spec['critics']) + 1 + len(spec['verifiers']) * spec['verificationRuns']
    return {'ok': True, 'goal': spec['goal'], 'acceptance': spec['acceptance'], 'inputs': inputs,
            'maximumCalls': per_round * spec['maxRounds'], 'maxRounds': spec['maxRounds'],
            'verificationRuns': spec['verificationRuns'], 'deadlineSeconds': spec['deadlineSeconds'],
            'commands': spec['proposers'] + spec['critics'] + [spec['aggregator']] + spec['verifiers'],
            'note': 'Inspection executes no adapters. Run executes these commands with inherited host permissions.'}


def audit(root):
    value = read_json(root / 'result.json')
    require(isinstance(value, dict) and type(value.get('schemaVersion')) is int and value['schemaVersion'] == 1 and
            value.get('kind') == 'moa-run' and value.get('status') in ('running', 'passed', 'failed', 'interrupted') and
            isinstance(value.get('artifacts'), list) and isinstance(value.get('inputs'), list) and
            text(value.get('workspace')), 'INVALID_RUN', 'Malformed MOA result; preserve the run directory.')
    for record in value['artifacts'] + value['inputs']:
        require(isinstance(record, dict) and text(record.get('path')) and type(record.get('bytes')) is int and
                record['bytes'] >= 0 and isinstance(record.get('sha256'), str) and
                re.fullmatch(r'[0-9a-f]{64}', record['sha256']) is not None,
                'INVALID_RUN', 'Malformed evidence record.')
    def valid(condition):
        require(condition, 'INVALID_RUN', 'Run evidence does not support the recorded acceptance.')

    workspace = Path(value['workspace'])
    valid(workspace.is_absolute() and value.get('mode') in ('run', 'recheck') and text(value.get('runId')))
    artifacts = {r['path']: r for r in value['artifacts']}
    valid(len(artifacts) == len(value['artifacts']) and 'spec.json' in artifacts)
    candidate = value.get('candidate')
    if candidate is not None:
        valid(isinstance(candidate, str) and candidate in artifacts and
              value.get('candidateSha256') == artifacts[candidate]['sha256'])
    artifact_issues, input_issues = changed(root, value['artifacts']), changed(workspace, value['inputs'])
    integrity = not artifact_issues and not input_issues
    if integrity and value['status'] == 'passed':
        spec = validate_spec(read_json(root / 'spec.json'), root)
        valid(value.get('acceptance') == spec['acceptance'] and value.get('goal') == spec['goal'] and candidate is not None)
        rounds, calls = value.get('rounds'), value.get('calls')
        valid(isinstance(rounds, list) and 1 <= len(rounds) <= spec['maxRounds'] and isinstance(calls, list))
        valid(all(isinstance(r, dict) and type(r.get('round')) is int and r['round'] == i + 1
                  for i, r in enumerate(rounds)))
        final = rounds[-1]
        valid(final.get('passed') is True and final.get('candidate') == candidate)
        valid(len(calls) <= inspect_spec(spec, value['inputs'])['maximumCalls'])
        receipts = set()
        for call in calls:
            valid(isinstance(call, dict) and call.get('role') in ('propose', 'critique', 'aggregate', 'verify') and
                  type(call.get('round')) is int and 1 <= call['round'] <= len(rounds) and
                  type(call.get('ok')) is bool and identifier(call.get('adapterId')))
            key = (call['role'], call['adapterId'], call['round'], call.get('verificationIndex'))
            valid(key not in receipts); receipts.add(key)
            valid(all(isinstance(call.get(k), str) and call[k] in artifacts for k in ('request', 'stdout', 'stderr')))
            request = read_json(root / call['request'])
            valid(isinstance(request, dict) and request.get('runId') == value['runId'] and
                  request.get('role') == call['role'] and request.get('adapterId') == call['adapterId'] and
                  request.get('round') == call['round'] and request.get('inputs') == value['inputs'] and
                  request.get('workspace') == value['workspace'])
            if call['ok']:
                valid(type(call.get('returnCode')) is int and call['returnCode'] == 0 and
                      type(call.get('pid')) is int and call['pid'] > 0)
                valid(isinstance(call.get('response'), dict) and read_json(root / call['stdout']) == call['response'])
        verifiers = {a['id']: a for a in spec['verifiers']}
        checks = [c for c in calls if c['role'] == 'verify' and c['round'] == final['round']]
        expected = {(key, i) for key in verifiers for i in range(1, spec['verificationRuns'] + 1)}
        valid({(c['adapterId'], c.get('verificationIndex')) for c in checks} == expected and len(checks) == len(expected))
        for call in checks:
            response = call.get('response')
            valid(call['ok'] and call.get('candidateSha256') == value['candidateSha256'] and isinstance(response, dict))
            request = read_json(root / call['request'])
            valid(isinstance(request.get('candidate'), dict) and request['candidate'].get('sha256') == value['candidateSha256'] and
                  request.get('verificationIndex') == call['verificationIndex'] and
                  request.get('covers') == verifiers[call['adapterId']]['covers'])
            actual = response.get('checks')
            valid(isinstance(actual, dict) and set(actual) == set(verifiers[call['adapterId']]['covers']) and
                  all(v is True for v in actual.values()))
        if value['mode'] == 'run':
            proposers = [c for c in calls if c['role'] == 'propose' and c['round'] == final['round']]
            valid({c['adapterId'] for c in proposers} == {a['id'] for a in spec['proposers']} and
                  sum(c['ok'] for c in proposers) >= spec['minProposals'])
            critics = [c for c in calls if c['role'] == 'critique' and c['round'] == final['round']]
            valid({c['adapterId'] for c in critics} == {a['id'] for a in spec['critics']} and all(c['ok'] for c in critics))
            aggregate = [c for c in calls if c['role'] == 'aggregate' and c['round'] == final['round']]
            valid(len(aggregate) == 1 and aggregate[0]['ok'] and aggregate[0]['adapterId'] == spec['aggregator']['id'])
            valid(aggregate[0]['response'].get('content', '').encode('utf-8') == (root / candidate).read_bytes())
        else:
            valid(isinstance(value.get('origin'), dict) and text(value['origin'].get('resultSha256')) and
                  all(c['role'] == 'verify' for c in calls))
    return {'ok': integrity and value['status'] == 'passed', 'integrityOk': integrity,
            'status': value['status'], 'artifactIssues': artifact_issues, 'inputIssues': input_issues}, value



class Engine:
    def __init__(self, spec, workspace, root, inputs, mode='run', origin=None):
        require(not root.exists() and not root.is_symlink(), 'RUN_EXISTS', 'Use a new run directory; existing evidence is never overwritten.')
        root = root.resolve()
        self.spec, self.workspace, self.root, self.inputs = spec, workspace, root, inputs
        self.records = {}
        self.deadline = time.monotonic() + spec['deadlineSeconds']
        self.semaphore = None
        self.result = {'schemaVersion': 1, 'kind': 'moa-run', 'runId': uuid.uuid4().hex,
                       'status': 'running', 'mode': mode, 'workspace': str(workspace), 'inputs': inputs,
                       'startedAt': now(), 'goal': spec['goal'], 'acceptance': spec['acceptance'],
                       'calls': [], 'rounds': [], 'degraded': False, 'candidate': None,
                       'candidateSha256': None, 'origin': origin, 'artifacts': []}
        require(not root.exists() and not root.is_symlink(), 'RUN_EXISTS', 'Use a new run directory; existing evidence is never overwritten.')
        root.mkdir(parents=True, exist_ok=False)
        self.write('spec.json', encoded(spec))
        self.checkpoint()

    def write(self, relative, data):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        self.records[relative] = pin(self.root, relative)
        return relative

    def checkpoint(self):
        self.result['artifacts'] = list(self.records.values())
        temporary = self.root / 'result.json.tmp'
        temporary.write_bytes(encoded(self.result))
        os.replace(temporary, self.root / 'result.json')

    def stable(self):
        require(not changed(self.workspace, self.inputs), 'INPUT_CHANGED', 'Source inputs changed; use a new reviewed input revision.')
        require(not changed(self.root, list(self.records.values())), 'EVIDENCE_CHANGED', 'Recorded run evidence changed during execution.')

    def request(self, role, adapter, round_number, feedback):
        previous = self.result['candidate']
        previous = dict(self.records[previous], path=str(self.root / previous)) if previous else None
        return {'protocolVersion': 1, 'runId': self.result['runId'], 'role': role, 'adapterId': adapter['id'],
                'round': round_number, 'goal': self.spec['goal'], 'acceptance': self.spec['acceptance'],
                'workspace': str(self.workspace), 'inputs': self.inputs, 'feedback': feedback,
                'runDirectory': str(self.root), 'previousCandidate': previous}

    async def invoke(self, adapter, request):
        async with self.semaphore:
            self.stable()
            remaining = self.deadline - time.monotonic()
            require(remaining > 0, 'RUN_DEADLINE', 'Run deadline exhausted; no further adapters started.')
            role, index = request['role'], request.get('verificationIndex')
            folder = 'r{}/{}-{}{}'.format(request['round'], role, adapter['id'], '-v' + str(index) if index else '')
            payload = encoded(request)
            require(len(payload) <= MAX_REQUEST, 'REQUEST_LIMIT', 'Adapter packet exceeded 512 KiB; split the task or use smaller reference outputs.')
            self.write(folder + '/request.json', payload)
            working = self.root / folder / 'work'; working.mkdir()
            record = {'adapterId': adapter['id'], 'role': role, 'round': request['round'],
                      'verificationIndex': index, 'argv': adapter['argv'], 'pid': None, 'returnCode': None,
                      'startedAt': now(), 'ok': False, 'response': None, 'error': None, 'request': folder + '/request.json'}
            if role == 'verify':
                record['candidateSha256'] = request['candidate']['sha256']
            captures = {'stdout': bytearray(), 'stderr': bytearray()}
            process, tasks = None, []
            started = time.monotonic()
            timeout = min(adapter['timeoutSeconds'], remaining)

            async def read(stream, name):
                while True:
                    chunk = await stream.read(8192)
                    if not chunk:
                        return
                    available = MAX_STREAM - len(captures[name])
                    captures[name].extend(chunk[:available])
                    require(len(chunk) <= available, 'OUTPUT_LIMIT', 'Adapter stdout or stderr exceeded 256 KiB.')

            async def send():
                try:
                    process.stdin.write(payload)
                    await process.stdin.drain()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    process.stdin.close()

            try:
                process = await asyncio.create_subprocess_exec(*adapter['argv'], cwd=str(working),
                            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE, start_new_session=(os.name == 'posix'))
                record['pid'] = process.pid
                tasks = [asyncio.create_task(send()), asyncio.create_task(read(process.stdout, 'stdout')),
                         asyncio.create_task(read(process.stderr, 'stderr')), asyncio.create_task(process.wait())]
                await asyncio.wait_for(asyncio.gather(*tasks), timeout=timeout)
                require(process.returncode == 0, 'ADAPTER_EXIT', 'Adapter returned a nonzero exit code; inspect stderr evidence.')
                response = json.loads(bytes(captures['stdout']).decode('utf-8'))
                require(isinstance(response, dict), 'INVALID_RESPONSE', 'Adapter must return one JSON object.')
                if role == 'verify':
                    checks = response.get('checks')
                    require(isinstance(checks, dict) and set(checks) == set(adapter['covers']) and
                            all(type(v) is bool for v in checks.values()) and
                            isinstance(response.get('findings'), list) and len(response['findings']) <= 50 and
                            all(text(f) and len(f.encode('utf-8')) <= 2048 for f in response['findings']),
                            'INVALID_RESPONSE', 'Verifier must return exactly its covered checks as booleans and a findings list.')
                else:
                    require(text(response.get('content')) and len(response['content'].encode('utf-8')) <= MAX_CONTENT,
                            'INVALID_RESPONSE', 'Proposer and aggregator content must be nonempty and at most 64 KiB.')
                record.update(ok=True, response=response)
            except asyncio.TimeoutError:
                record['error'] = {'code': 'RUN_DEADLINE' if remaining <= adapter['timeoutSeconds'] else 'ADAPTER_TIMEOUT',
                                   'message': 'Adapter deadline reached; execution was stopped.'}
            except BoardError as error:
                record['error'] = {'code': error.code, 'message': error.message}
            except (UnicodeError, ValueError):
                record['error'] = {'code': 'INVALID_RESPONSE', 'message': 'Adapter output was not one UTF-8 JSON object.'}
            except OSError:
                record['error'] = {'code': 'ADAPTER_LAUNCH', 'message': 'Could not launch the declared command.'}
            finally:
                if process is not None:
                    # Each POSIX adapter owns a new process group. No external PIDs are targeted.
                    try:
                        if os.name == 'posix':
                            os.killpg(process.pid, signal.SIGKILL)
                        elif process.returncode is None:
                            process.kill()
                    except ProcessLookupError:
                        pass
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)

                    async def drain(stream):
                        while await stream.read(8192):
                            pass
                    try:
                        await asyncio.wait_for(asyncio.gather(drain(process.stdout), drain(process.stderr), process.wait()), 1)
                    except asyncio.TimeoutError:
                        record.update(ok=False, error={'code': 'CLEANUP_UNKNOWN', 'message': 'Adapter pipes did not settle; inspect its real execution before retrying.'})
                    record['returnCode'] = process.returncode
                record['durationMs'] = round((time.monotonic() - started) * 1000)
                for name, data in captures.items():
                    record[name] = self.write(folder + '/' + name + '.txt', bytes(data))
                self.result['calls'].append(record)
                self.checkpoint()
            self.stable()
            return record

    async def verify_candidate(self, round_number, candidate, feedback):
        records = []
        for index in range(1, self.spec['verificationRuns'] + 1):
            for adapter in self.spec['verifiers']:
                request = self.request('verify', adapter, round_number, feedback)
                request.update(candidate=dict(candidate, path=str(self.root / candidate['path'])), verificationIndex=index,
                               covers=adapter['covers'])
                record = await self.invoke(adapter, request)
                records.append(record)
                require(record['ok'], 'VERIFICATION_EXECUTION', 'A verifier could not execute correctly; inspect its recorded failure.')
        return records

    async def run(self, initial_candidate=None):
        self.semaphore = asyncio.Semaphore(self.spec['maxParallel'])
        feedback, failed_versions = [], set()
        for round_number in range(1, (1 if initial_candidate is not None else self.spec['maxRounds']) + 1):
            self.stable()
            current = {'round': round_number, 'passed': False, 'candidate': None, 'verificationCalls': []}
            self.result['rounds'].append(current)
            if initial_candidate is None:
                calls = await asyncio.gather(*[self.invoke(a, self.request('propose', a, round_number, feedback))
                                              for a in self.spec['proposers']], return_exceptions=True)
                for call in calls:
                    if isinstance(call, BaseException):
                        raise call
                proposals = [c for c in calls if c['ok']]
                self.result['degraded'] = self.result['degraded'] or len(proposals) < len(calls)
                require(len(proposals) >= self.spec['minProposals'], 'PROPOSAL_QUORUM', 'Too few valid proposals; aggregation was not started.')
                proposal_packet = [{'id': c['adapterId'], 'response': c['response']} for c in proposals]
                async def critique(adapter):
                    request = self.request('critique', adapter, round_number, feedback)
                    request['proposals'] = proposal_packet
                    return await self.invoke(adapter, request)
                criticisms = await asyncio.gather(*[critique(a) for a in self.spec['critics']], return_exceptions=True)
                for record in criticisms:
                    if isinstance(record, BaseException):
                        raise record
                require(all(c['ok'] for c in criticisms), 'CRITIQUE_EXECUTION', 'A declared critic failed; aggregation was not started.')
                request = self.request('aggregate', self.spec['aggregator'], round_number, feedback)
                request['proposals'] = proposal_packet
                request['critiques'] = [{'id': c['adapterId'], 'response': c['response']} for c in criticisms]
                aggregate = await self.invoke(self.spec['aggregator'], request)
                require(aggregate['ok'], 'AGGREGATION_EXECUTION', 'Aggregator failed; inspect its recorded outcome.')
                candidate_bytes = aggregate['response']['content'].encode('utf-8')
            else:
                candidate_bytes = initial_candidate
            filename = self.write('r{}/candidate.txt'.format(round_number), candidate_bytes)
            candidate = self.records[filename]
            require(candidate['sha256'] not in failed_versions, 'NO_PROGRESS',
                    'This candidate already failed; a changed candidate is required before more verification.')
            current['candidate'] = filename
            self.result.update(candidate=filename, candidateSha256=candidate['sha256'])
            checks = await self.verify_candidate(round_number, candidate, feedback)
            current['verificationCalls'] = [{'adapterId': c['adapterId'], 'verificationIndex': c['verificationIndex'],
                                             'checks': c['response']['checks'], 'stdout': c['stdout']} for c in checks]
            current['passed'] = all(all(c['response']['checks'].values()) for c in checks)
            self.checkpoint()
            if current['passed']:
                self.stable()
                self.result['status'] = 'passed'
                return
            failed_versions.add(candidate['sha256'])
            feedback = [{'adapterId': c['adapterId'], 'checks': c['response']['checks'],
                         'findings': c['response']['findings'][:10], 'evidence': str(self.root / c['stdout'])}
                        for c in checks if not all(c['response']['checks'].values())]
        raise BoardError('ACCEPTANCE_FAILED', 'Checks did not all pass on one candidate within the round budget.')

    async def finish(self, candidate=None):
        try:
            await self.run(candidate)
        except BoardError as error:
            self.result.update(status='failed', error={'code': error.code, 'message': error.message})
        except asyncio.CancelledError:
            self.result.update(status='interrupted', error={'code': 'INTERRUPTED', 'message': 'Execution interrupted; inspect actual handles before another run.'})
            raise
        finally:
            self.result['finishedAt'] = now()
            self.checkpoint()
        return {'ok': self.result['status'] == 'passed', 'status': self.result['status'],
                'runDir': str(self.root), 'result': str(self.root / 'result.json'),
                'candidate': str(self.root / self.result['candidate']) if self.result['candidate'] else None,
                'degraded': self.result['degraded'], 'error': self.result.get('error')}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    for command in ('inspect', 'run'):
        entry = sub.add_parser(command)
        entry.add_argument('--spec', required=True, type=Path)
        entry.add_argument('--workspace', required=True, type=Path)
        if command == 'run':
            entry.add_argument('--run-dir', required=True, type=Path)
    entry = sub.add_parser('audit'); entry.add_argument('--run-dir', required=True, type=Path)
    entry = sub.add_parser('recheck'); entry.add_argument('--source-run', required=True, type=Path)
    entry.add_argument('--run-dir', required=True, type=Path); entry.add_argument('--runs', type=int)
    return p


def main():
    try:
        args = parser().parse_args()
        if args.command == 'audit':
            result, _ = audit(args.run_dir.expanduser().resolve())
            code = 0 if result['ok'] else 1
        else:
            candidate, origin = None, None
            if args.command == 'recheck':
                root = args.source_run.expanduser().resolve()
                report, old = audit(root)
                require(report['ok'], 'SOURCE_RUN_INVALID', 'Recheck requires an accepted source run with unchanged evidence and inputs.')
                spec = validate_spec(read_json(root / 'spec.json'), root)
                workspace, inputs = Path(old['workspace']), old['inputs']
                if args.runs is not None:
                    require(integer(args.runs, 1, 5), 'INVALID_SPEC', 'Recheck runs must be between 1 and 5.')
                    spec['verificationRuns'] = args.runs
                candidate = (root / old['candidate']).read_bytes()
                require(hashlib.sha256(candidate).hexdigest() == old['candidateSha256'], 'SOURCE_RUN_INVALID', 'Source candidate changed.')
                origin = {'runId': old['runId'], 'resultSha256': hashlib.sha256((root / 'result.json').read_bytes()).hexdigest(),
                          'sourceRun': str(root)}
            else:
                file = args.spec.expanduser().resolve()
                spec = validate_spec(read_json(file), file.parent)
                workspace = args.workspace.expanduser().resolve()
                inputs = source_inputs(spec, workspace)
            if args.command == 'inspect':
                result, code = inspect_spec(spec, inputs), 0
            else:
                target = args.run_dir.expanduser().absolute()
                engine = Engine(spec, workspace, target, inputs, 'recheck' if candidate is not None else 'run', origin)
                result = asyncio.run(engine.finish(candidate))
                code = 0 if result['ok'] else 1
    except BoardError as error:
        result, code = {'ok': False, 'error': {'code': error.code, 'message': error.message}}, 2
    except (OSError, ValueError, KeyError, TypeError, UnicodeError):
        result, code = {'ok': False, 'error': {'code': 'MOA_IO_OR_FORMAT', 'message': 'MOA I/O or format failure; inspect existing evidence.'}}, 2
    except KeyboardInterrupt:
        result, code = {'ok': False, 'error': {'code': 'INTERRUPTED', 'message': 'Inspect persisted evidence and real execution before resuming.'}}, 130
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(main())

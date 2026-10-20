# SPDX-License-Identifier: MIT
"""MOA behavior with actual subprocess adapters, files, and failure injection."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import moa

SCRIPT = Path(__file__).with_name('moa.py')
ADAPTER = Path(__file__).with_name('moa_demo_adapter.py')


class MoaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bot-moa-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'amounts.json').write_text(json.dumps({'amounts': [17, 25]}))
        self.spec = {'schemaVersion': 1, 'goal': 'Retain source amounts and compute the total',
                     'acceptance': {'total': 'Recompute total from source', 'values': 'Preserve both source amounts'},
                     'inputs': ['amounts.json'], 'proposers': [self.adapter('direct'), self.adapter('sorted', 'sorted')],
                     'aggregator': self.adapter('merge'), 'verifiers': [dict(self.adapter('check'), covers=['total', 'values'])],
                     'maxRounds': 2, 'verificationRuns': 2, 'maxParallel': 2, 'deadlineSeconds': 20}

    def adapter(self, key, mode='normal'):
        return {'id': key, 'argv': [sys.executable, str(ADAPTER), mode], 'timeoutSeconds': 3}

    def call(self, command, *args, code=0, error=None):
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), command, *map(str, args)],
                                capture_output=True, text=True, timeout=30)
        self.assertNotIn('Traceback', result.stderr, result.stderr)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        value = json.loads(result.stdout)
        if error:
            self.assertEqual(value['error']['code'], error)
        return value

    def run_moa(self, code=0, name='run'):
        spec = self.root / 'spec.json'; spec.write_text(json.dumps(self.spec))
        return self.call('run', '--spec', spec, '--workspace', self.root, '--run-dir', self.root / name, code=code)

    def record(self, name='run'):
        return json.loads((self.root / name / 'result.json').read_text())

    def test_real_pipeline_repeats_checks_on_same_candidate(self):
        result = self.run_moa(); record = self.record()
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(json.loads((self.root / 'run' / record['candidate']).read_text())['total'], 42)
        self.assertEqual([c['role'] for c in record['calls']].count('propose'), 2)
        checks = [c for c in record['calls'] if c['role'] == 'verify']
        self.assertEqual(len(checks), 2)
        self.assertTrue(all(c['returnCode'] == 0 and c['pid'] > 0 for c in record['calls']))
        self.assertEqual(len({c['candidateSha256'] for c in checks}), 1)
        self.assertTrue(self.call('audit', '--run-dir', self.root / 'run')['integrityOk'])

    def test_failed_first_round_is_preserved_and_feedback_repairs_second(self):
        self.spec['aggregator'] = self.adapter('merge', 'repair'); self.run_moa()
        record = self.record()
        self.assertEqual([r['passed'] for r in record['rounds']], [False, True])
        self.assertEqual(len([c for c in record['calls'] if c['role'] == 'aggregate']), 2)
        request = json.loads((self.root / 'run/r2/aggregate-merge/request.json').read_text())
        self.assertTrue(request['feedback'])

    def test_round_budget_never_converts_failed_checks_into_acceptance(self):
        self.spec['aggregator'] = self.adapter('merge', 'always-wrong'); self.run_moa(code=1)
        record = self.record()
        self.assertEqual(record['status'], 'failed')
        self.assertEqual(len(record['rounds']), 2)
        self.assertFalse(any(r['passed'] for r in record['rounds']))

    def test_flaky_second_check_prevents_acceptance(self):
        self.spec['maxRounds'] = 1; self.spec['verifiers'][0]['argv'][-1] = 'flaky'
        self.run_moa(code=1)
        self.assertEqual([c['response']['checks']['total'] for c in self.record()['calls'] if c['role'] == 'verify'], [True, False])

    def test_failed_proposer_blocks_aggregation_without_quorum(self):
        self.spec['proposers'][0]['argv'][-1] = 'crash'; self.run_moa(code=1)
        record = self.record()
        self.assertFalse(any(c['role'] == 'aggregate' for c in record['calls']))
        self.assertEqual(record['error']['code'], 'PROPOSAL_QUORUM')

    def test_explicit_partial_quorum_reports_degradation(self):
        self.spec['minProposals'] = 1; self.spec['proposers'][0]['argv'][-1] = 'crash'
        self.run_moa(); self.assertTrue(self.record()['degraded'])
        self.assertEqual(len([c for c in self.record()['calls'] if not c['ok']]), 1)

    def test_non_json_proposal_does_not_become_a_candidate(self):
        self.spec['proposers'][0]['argv'][-1] = 'invalid'; self.run_moa(code=1)
        failed = [c for c in self.record()['calls'] if not c['ok']]
        self.assertEqual(failed[0]['error']['code'], 'INVALID_RESPONSE')

    def test_uncovered_acceptance_is_rejected_before_execution(self):
        self.spec['verifiers'][0]['covers'] = ['total']
        spec = self.root / 'spec.json'; spec.write_text(json.dumps(self.spec))
        self.call('run', '--spec', spec, '--workspace', self.root, '--run-dir', self.root / 'run',
                  code=2, error='UNCOVERED_ACCEPTANCE')
        self.assertFalse((self.root / 'run').exists())

    def test_boolean_budget_and_duplicate_ids_are_invalid(self):
        for change in ('boolean', 'duplicate'):
            with self.subTest(change=change):
                spec = json.loads(json.dumps(self.spec))
                if change == 'boolean':
                    spec['maxRounds'] = True
                else:
                    spec['aggregator']['id'] = 'direct'
                path = self.root / 'bad.json'; path.write_text(json.dumps(spec))
                self.call('inspect', '--spec', path, '--workspace', self.root, code=2, error='INVALID_SPEC')

    def test_inspect_is_read_only_and_reports_maximum_calls(self):
        path = self.root / 'spec.json'; path.write_text(json.dumps(self.spec))
        before = set(self.root.iterdir())
        result = self.call('inspect', '--spec', path, '--workspace', self.root)
        self.assertEqual(result['maximumCalls'], 10)
        self.assertEqual(set(self.root.iterdir()), before)

    def test_timeout_records_actual_process_outcome(self):
        self.spec['proposers'][0].update(argv=[sys.executable, str(ADAPTER), 'sleep'], timeoutSeconds=0.2)
        self.run_moa(code=1)
        failed = [c for c in self.record()['calls'] if not c['ok']][0]
        self.assertEqual(failed['error']['code'], 'ADAPTER_TIMEOUT')
        self.assertIsNotNone(failed['returnCode'])

    def test_output_limit_is_fail_closed(self):
        self.spec['proposers'][0]['argv'][-1] = 'flood'; self.run_moa(code=1)
        failed = [c for c in self.record()['calls'] if not c['ok']][0]
        self.assertEqual(failed['error']['code'], 'OUTPUT_LIMIT')
        stdout = self.root / 'run' / failed['stdout']
        self.assertLessEqual(stdout.stat().st_size, 256 * 1024)

    @unittest.skipUnless(os.name == 'posix', 'POSIX process groups only')
    def test_cleanup_signal_error_preserves_output_limit_and_records_uncertainty(self):
        workspace = self.root.resolve()
        spec = moa.validate_spec(self.spec, workspace)
        adapter = dict(spec['proposers'][0], argv=[sys.executable, str(ADAPTER), 'flood'])
        engine = moa.Engine(spec, workspace, workspace / 'signal-error', moa.source_inputs(spec, workspace))

        async def invoke():
            engine.semaphore = asyncio.Semaphore(1)
            with mock.patch.object(moa.os, 'killpg', side_effect=PermissionError('synthetic signal denial')):
                return await engine.invoke(adapter, engine.request('propose', adapter, 1, []))

        record = asyncio.run(invoke())
        self.assertFalse(record['ok'])
        self.assertEqual(record['error']['code'], 'OUTPUT_LIMIT')
        self.assertEqual(record['cleanupError']['code'], 'CLEANUP_SIGNAL')
        self.assertIsNotNone(record['returnCode'])
        self.assertLessEqual((engine.root / record['stdout']).stat().st_size, 256 * 1024)
        saved = json.loads((engine.root / 'result.json').read_text())
        self.assertEqual(saved['calls'][0]['cleanupError']['code'], 'CLEANUP_SIGNAL')

    @unittest.skipUnless(os.name == 'posix', 'POSIX process groups only')
    def test_cleanup_signal_error_cannot_accept_a_valid_response(self):
        workspace = self.root.resolve()
        spec = moa.validate_spec(self.spec, workspace)
        engine = moa.Engine(spec, workspace, workspace / 'valid-signal-error', moa.source_inputs(spec, workspace))
        adapter = spec['proposers'][0]

        async def invoke():
            engine.semaphore = asyncio.Semaphore(1)
            with mock.patch.object(moa.os, 'killpg', side_effect=PermissionError('synthetic signal denial')):
                return await engine.invoke(adapter, engine.request('propose', adapter, 1, []))

        record = asyncio.run(invoke())
        self.assertFalse(record['ok'])
        self.assertIsNotNone(record['response'])
        self.assertEqual(record['error']['code'], 'CLEANUP_UNKNOWN')
        self.assertEqual(record['cleanupError']['code'], 'CLEANUP_SIGNAL')
        self.assertEqual(record['returnCode'], 0)

    def test_verifier_cannot_omit_a_required_check(self):
        self.spec['verifiers'][0]['argv'][-1] = 'missing-check'; self.run_moa(code=1)
        failed = [c for c in self.record()['calls'] if not c['ok']]
        self.assertEqual(failed[0]['error']['code'], 'INVALID_RESPONSE')

    def test_verifier_mutating_candidate_prevents_acceptance(self):
        self.spec['verifiers'][0]['argv'][-1] = 'mutate'; self.run_moa(code=1)
        self.assertEqual(self.record()['error']['code'], 'EVIDENCE_CHANGED')

    def test_verifier_mutating_inputs_prevents_acceptance(self):
        self.spec['verifiers'][0]['argv'][-1] = 'change-input'; self.run_moa(code=1)
        self.assertEqual(self.record()['error']['code'], 'INPUT_CHANGED')

    def test_audit_detects_later_candidate_and_source_changes(self):
        self.run_moa(); candidate = self.root / 'run' / self.record()['candidate']
        original = candidate.read_text(); candidate.write_text('changed')
        result = self.call('audit', '--run-dir', self.root / 'run', code=1)
        self.assertFalse(result['integrityOk'])
        candidate.write_text(original); (self.root / 'amounts.json').write_text('{"amounts": [99]}')
        result = self.call('audit', '--run-dir', self.root / 'run', code=1)
        self.assertTrue(result['inputIssues'])

    def test_recheck_runs_only_verifiers_and_preserves_candidate_digest(self):
        self.run_moa()
        self.call('recheck', '--source-run', self.root / 'run', '--run-dir', self.root / 'recheck', '--runs', '3')
        old, new = self.record(), self.record('recheck')
        self.assertEqual([c['role'] for c in new['calls']], ['verify'] * 3)
        self.assertEqual(new['candidateSha256'], old['candidateSha256'])
        self.assertTrue(new['origin']['resultSha256'])
        self.assertEqual(new['status'], 'passed')

    def test_recheck_refuses_stale_source_without_new_execution(self):
        self.run_moa(); (self.root / 'amounts.json').write_text('{"amounts": [99]}')
        self.call('recheck', '--source-run', self.root / 'run', '--run-dir', self.root / 'recheck',
                  code=2, error='SOURCE_RUN_INVALID')
        self.assertFalse((self.root / 'recheck').exists())

    def test_queued_proposals_obey_parallel_limit(self):
        self.spec['proposers'].append(self.adapter('third'))
        self.spec['maxParallel'] = 1
        self.run_moa()
        self.assertEqual(len([c for c in self.record()['calls'] if c['role'] == 'propose']), 3)

    def test_computation_uses_actual_input_instead_of_a_canned_answer(self):
        (self.root / 'amounts.json').write_text(json.dumps({'amounts': [4, -7, 0, 100]}))
        self.run_moa(); record = self.record()
        candidate = json.loads((self.root / 'run' / record['candidate']).read_text())
        self.assertEqual(candidate, {'amounts': [4, -7, 0, 100], 'total': 97})

    def test_failed_result_cannot_be_promoted_by_editing_status(self):
        self.spec['maxRounds'] = 1; self.spec['aggregator'] = self.adapter('merge', 'always-wrong')
        self.run_moa(code=1); value = self.record(); value['status'] = 'passed'
        (self.root / 'run/result.json').write_text(json.dumps(value))
        self.call('audit', '--run-dir', self.root / 'run', code=2, error='INVALID_RUN')

    def test_missing_repeat_receipt_cannot_pass_audit(self):
        self.run_moa(); value = self.record()
        value['calls'] = [c for c in value['calls'] if not (c['role'] == 'verify' and c['verificationIndex'] == 2)]
        (self.root / 'run/result.json').write_text(json.dumps(value))
        self.call('audit', '--run-dir', self.root / 'run', code=2, error='INVALID_RUN')

    def test_candidate_path_outside_run_is_rejected(self):
        self.run_moa(); value = self.record(); value['candidate'] = '../amounts.json'
        (self.root / 'run/result.json').write_text(json.dumps(value))
        self.call('audit', '--run-dir', self.root / 'run', code=2, error='INVALID_RUN')

    @unittest.skipUnless(os.name == 'posix', 'POSIX owned process group check')
    def test_timeout_stops_owned_descendant_process(self):
        self.spec['proposers'][0].update(argv=[sys.executable, str(ADAPTER), 'descendant'], timeoutSeconds=0.3)
        self.run_moa(code=1)
        child = (self.root / 'run/r1/propose-direct/work/child.pid').read_text()
        result = subprocess.run(['ps', '-p', child, '-o', 'stat='], capture_output=True, text=True, timeout=3)
        self.assertTrue(not result.stdout.strip() or result.stdout.strip().startswith('Z'), result.stdout)

    def test_cross_review_receipt_is_supplied_to_aggregator(self):
        self.spec['critics'] = [self.adapter('crosscheck')]
        self.run_moa(); record = self.record()
        roles = [c['role'] for c in record['calls']]
        self.assertLess(roles.index('critique'), roles.index('aggregate'))
        request = json.loads((self.root / 'run/r1/aggregate-merge/request.json').read_text())
        self.assertEqual(request['critiques'][0]['id'], 'crosscheck')

    def test_critic_uses_source_to_reject_a_wrong_candidate(self):
        self.spec['critics'] = [self.adapter('crosscheck')]
        self.spec['proposers'][0]['argv'][-1] = 'wrong'
        self.run_moa(); record = self.record()
        critique = [c['response'] for c in record['calls'] if c['role'] == 'critique'][0]
        self.assertEqual(json.loads(critique['content'])['invalidCandidateIds'], ['direct'])
        candidate = json.loads((self.root / 'run' / record['candidate']).read_text())
        self.assertEqual(candidate['total'], 42)

    def test_failed_declared_critic_blocks_aggregation(self):
        self.spec['critics'] = [self.adapter('crosscheck', 'crash')]
        self.run_moa(code=1)
        self.assertFalse(any(c['role'] == 'aggregate' for c in self.record()['calls']))
        self.assertEqual(self.record()['error']['code'], 'CRITIQUE_EXECUTION')

    def test_unchanged_failed_candidate_is_not_retried_until_lucky(self):
        self.spec['verifiers'][0]['argv'][-1] = 'first-round-fails'
        self.run_moa(code=1)
        self.assertEqual(self.record()['error']['code'], 'NO_PROGRESS')
        self.assertEqual(len([c for c in self.record()['calls'] if c['role'] == 'verify']), 2)

    def test_existing_run_directory_is_not_overwritten(self):
        self.run_moa(); before = (self.root / 'run/result.json').read_bytes()
        self.run_moa(code=2)
        self.assertEqual((self.root / 'run/result.json').read_bytes(), before)

    def test_corrupt_result_is_structured_error(self):
        run = self.root / 'run'; run.mkdir(); (run / 'result.json').write_text('[]')
        self.call('audit', '--run-dir', run, code=2, error='INVALID_RUN')


if __name__ == '__main__':
    unittest.main(verbosity=2)

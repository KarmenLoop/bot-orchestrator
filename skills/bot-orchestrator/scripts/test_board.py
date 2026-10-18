# SPDX-License-Identifier: MIT
"""Behavioral checks; all artifacts stay in isolated temporary directories."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('board.py')


class BoardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bot-orchestrator-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = [sys.executable, str(SCRIPT), '--db', str(self.root / 'board.sqlite3')]
        self.call('init', '--workspace', str(self.root), '--goal', 'Deliver a verified result',
                  '--acceptance', 'Both artifacts and final check agree')

    def call(self, *args, code=0, error=None):
        result = subprocess.run(self.base + list(args), capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        value = json.loads(result.stdout)
        if error:
            self.assertEqual(value['error']['code'], error)
        return value

    def save(self, name, text='actual artifact'):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')

    def add(self, key, *options):
        return self.call('add', key, '--objective', 'Produce ' + key,
                         '--check', 'Artifact content checked', '--deliverable', key + '.txt', *options)

    def finish(self, key):
        self.call('start', key)
        self.save(key + '.txt', 'verified ' + key)
        self.save(key + '-check.txt', 'actual check ' + key)
        self.call('submit', key, '--evidence', key + '-check.txt', '--note', 'Checks executed')
        self.save(key + '-review.txt', 'read back and reviewed ' + key)
        self.call('review', key, '--decision', 'accept', '--evidence', key + '-review.txt', '--reason', 'Checked content')

    def test_complete_goal_requires_real_files_review_and_final_evidence(self):
        self.add('a'); self.add('b', '--depends', 'a')
        self.finish('a'); self.finish('b')
        self.assertTrue(self.call('verify')['ok'])
        self.save('final.txt', 'both checked')
        self.call('close', '--evidence', 'final.txt', '--reason', 'All user checks passed')
        self.assertEqual(self.call('status')['status'], 'done')
        self.call('add', 'extra', '--objective', 'extra', '--check', 'checked', '--deliverable', 'extra.txt',
                  code=2, error='BOARD_CLOSED')

    def test_dependency_must_be_accepted_before_start(self):
        self.add('a'); self.add('b', '--depends', 'a')
        self.call('start', 'b', code=2, error='DEPENDENCY_PENDING')
        self.assertEqual(self.call('status')['tasks'][1]['attempts'], 0)

    def test_unknown_dependencies_do_not_create_tasks(self):
        before = self.call('status')['revision']
        self.call('add', 'b', '--objective', 'b', '--check', 'checked', '--deliverable', 'b.txt',
                  '--depends', 'unknown', code=2, error='UNKNOWN_DEPENDENCY')
        state = self.call('status')
        self.assertEqual(state['revision'], before)
        self.assertEqual(state['tasks'], [])

    def test_submission_does_not_mean_acceptance_and_requires_artifact(self):
        self.add('a'); self.call('start', 'a'); self.save('check.txt')
        self.call('submit', 'a', '--evidence', 'check.txt', '--note', 'missing deliverable',
                  code=2, error='EVIDENCE_UNREADABLE')
        self.assertEqual(self.call('status')['tasks'][0]['status'], 'running')
        self.save('a.txt')
        self.call('submit', 'a', '--evidence', 'check.txt', '--note', 'real deliverable')
        self.assertEqual(self.call('status')['tasks'][0]['status'], 'review')

    def test_changed_submitted_artifact_is_not_accepted(self):
        self.add('a'); self.call('start', 'a')
        self.save('a.txt'); self.save('check.txt'); self.save('review.txt')
        self.call('submit', 'a', '--evidence', 'check.txt', '--note', 'submitted')
        self.save('a.txt', 'different content')
        self.call('review', 'a', '--decision', 'accept', '--evidence', 'review.txt', '--reason', 'attempt',
                  code=2, error='EVIDENCE_CHANGED')

    def test_changed_accepted_dependency_blocks_downstream(self):
        self.add('a'); self.add('b', '--depends', 'a'); self.finish('a')
        self.save('a.txt', 'late change')
        self.call('start', 'b', code=2, error='DEPENDENCY_CHANGED')
        result = self.call('verify', code=1)
        self.assertEqual(result['issues'][0]['path'], 'a.txt')

    def test_reopen_invalidates_transitive_descendants_and_preserves_previous(self):
        self.add('a'); self.add('b', '--depends', 'a'); self.add('c', '--depends', 'b')
        self.finish('a'); self.finish('b'); self.finish('c')
        self.save('final.txt'); self.call('close', '--evidence', 'final.txt', '--reason', 'Checked')
        self.call('reopen', 'a', '--reason', 'New input version')
        state = self.call('status', '--full')
        self.assertEqual(state['status'], 'open')
        self.assertEqual([state['tasks'][x]['status'] for x in ['a', 'b', 'c']], ['pending', 'blocked', 'blocked'])
        self.assertEqual(len(state['tasks']['a']['previous']), 1)
        self.call('resume', 'b', '--reason', 'too early', code=2, error='DEPENDENCY_PENDING')

    def test_declared_write_scope_is_exclusive_across_processes(self):
        self.add('a', '--write', 'shared'); self.add('b', '--write', 'shared/result.txt')
        left = subprocess.Popen(self.base + ['start', 'a'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        right = subprocess.Popen(self.base + ['start', 'b'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        outputs = [left.communicate(timeout=10), right.communicate(timeout=10)]
        self.assertEqual(sorted([left.returncode, right.returncode]), [0, 2])
        rejected = [json.loads(out) for out, _ in outputs if not json.loads(out).get('ok')]
        self.assertEqual(rejected[0]['error']['code'], 'WRITE_CONFLICT')
        self.assertEqual(sum(t['status'] == 'running' for t in self.call('status')['tasks']), 1)

    def test_wait_time_does_not_schedule_or_resume(self):
        self.add('a')
        self.call('mark', 'a', '--state', 'waiting', '--reason', 'Wait for event', '--wake-at', '2026-10-20T09:00:00+08:00')
        self.assertEqual(self.call('due', '--now', '2026-10-20T00:59:59Z')['due'], [])
        self.assertEqual(self.call('due', '--now', '2026-10-20T01:00:00Z')['due'], ['a'])
        self.assertEqual(self.call('status')['tasks'][0]['status'], 'waiting')
        self.call('resume', 'a', '--reason', 'Actual event received')
        self.assertEqual(self.call('status')['tasks'][0]['status'], 'pending')

    def test_naive_time_rejected_without_state_change(self):
        self.add('a')
        self.call('mark', 'a', '--state', 'waiting', '--reason', 'Event', '--wake-at', '2026-10-20T09:00:00',
                  code=2, error='TIMEZONE_REQUIRED')
        self.assertEqual(self.call('status')['tasks'][0]['status'], 'pending')

    def test_attempt_budget_is_not_reset_by_rework(self):
        self.add('a', '--max-attempts', '1'); self.call('start', 'a')
        self.save('a.txt'); self.save('check.txt'); self.save('problems.txt')
        self.call('submit', 'a', '--evidence', 'check.txt', '--note', 'submitted')
        self.call('review', 'a', '--decision', 'rework', '--evidence', 'problems.txt', '--reason', 'Mismatch')
        self.call('start', 'a', code=2, error='ATTEMPT_BUDGET')

    def test_cancelled_required_work_cannot_close_goal(self):
        self.add('a'); self.call('mark', 'a', '--state', 'cancelled', '--reason', 'User cancelled')
        self.save('final.txt')
        self.call('close', '--evidence', 'final.txt', '--reason', 'attempt', code=2, error='REQUIRED_WORK_OPEN')

    def test_cancelled_optional_submission_is_not_a_required_evidence_gate(self):
        self.add('a'); self.add('optional', '--optional'); self.finish('a')
        self.call('start', 'optional'); self.save('optional.txt'); self.save('check.txt')
        self.call('submit', 'optional', '--evidence', 'check.txt', '--note', 'draft')
        self.call('mark', 'optional', '--state', 'cancelled', '--reason', 'Optional exploration ended')
        (self.root / 'optional.txt').unlink()
        self.save('final.txt')
        self.call('close', '--evidence', 'final.txt', '--reason', 'Required result checked')

    def test_parent_traversal_and_symlink_escape_rejected(self):
        self.call('add', 'a', '--objective', 'a', '--check', 'checked', '--deliverable', '../outside.txt',
                  code=2, error='INVALID_PATH')
        if hasattr(os, 'symlink'):
            (self.root / 'escape').symlink_to(self.root.parent, target_is_directory=True)
            self.call('add', 'a', '--objective', 'a', '--check', 'checked', '--deliverable', 'escape/outside.txt',
                      code=2, error='OUTSIDE_WORKSPACE')

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX FIFO check')
    def test_fifo_evidence_is_rejected_without_hanging(self):
        self.add('a'); self.call('start', 'a'); self.save('a.txt')
        os.mkfifo(self.root / 'fifo')
        self.call('submit', 'a', '--evidence', 'fifo', '--note', 'invalid input', code=2, error='INVALID_EVIDENCE')

    def test_existing_board_never_overwritten_and_recovers_across_processes(self):
        self.add('a'); self.call('start', 'a')
        self.call('init', '--workspace', str(self.root), '--goal', 'different', '--acceptance', 'different',
                  code=2, error='BOARD_EXISTS')
        state = self.call('status', '--full')
        self.assertEqual(state['goal'], 'Deliver a verified result')
        self.assertEqual(state['tasks']['a']['status'], 'running')
        self.assertEqual(state['tasks']['a']['attempts'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)

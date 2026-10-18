# SPDX-License-Identifier: MIT
"""Repository-tool regressions, using disposable copies and no network."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bot-package-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'source'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git', '__pycache__'))

    def call(self, script, *args):
        result = subprocess.run([sys.executable, '-B', str(self.root / 'scripts' / script), *args],
                                capture_output=True, text=True, timeout=15)
        self.assertNotIn('Traceback', result.stderr, result.stderr)
        return result, json.loads(result.stdout)

    def test_install_copies_complete_skill_without_overwriting(self):
        target = Path(self.temp.name) / 'installed'
        result, value = self.call('install_skill.py', '--destination', str(target))
        self.assertEqual(result.returncode, 0, value)
        self.assertEqual((target / 'SKILL.md').read_bytes(),
                         (self.root / 'skills/bot-orchestrator/SKILL.md').read_bytes())
        self.assertTrue((target / 'LICENSE').is_file())
        (target / 'keep.txt').write_text('keep')
        result, value = self.call('install_skill.py', '--destination', str(target))
        self.assertEqual(result.returncode, 2, value)
        self.assertEqual(value['error'], 'DESTINATION_EXISTS')
        self.assertEqual((target / 'keep.txt').read_text(), 'keep')

    def test_install_inside_source_is_rejected_before_copy_or_mkdir(self):
        spec = importlib.util.spec_from_file_location('isolated_installer', self.root / 'scripts/install_skill.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        target = self.root / 'skills/bot-orchestrator/nested/installation'
        with mock.patch.object(sys, 'argv', ['install_skill.py', '--destination', str(target)]), \
                mock.patch.object(module.shutil, 'copytree') as copier, mock.patch('builtins.print') as output:
            self.assertEqual(module.main(), 2)
            copier.assert_not_called()
            self.assertEqual(json.loads(output.call_args[0][0])['error'], 'DESTINATION_INSIDE_SOURCE')
        self.assertFalse(target.parent.exists())

    def test_install_resolved_alias_inside_source_is_rejected(self):
        alias = Path(self.temp.name) / 'alias'
        try:
            alias.symlink_to(self.root / 'skills/bot-orchestrator', target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest('Symlink creation unavailable: ' + str(error))
        result, value = self.call('install_skill.py', '--destination', str(alias / 'nested'))
        self.assertEqual(result.returncode, 2, value)
        self.assertEqual(value['error'], 'DESTINATION_INSIDE_SOURCE')
        self.assertFalse((alias / 'nested').exists())

    def test_checker_missing_core_files_returns_structured_failure(self):
        for name in ['skills/bot-orchestrator/SKILL.md', 'skills/bot-orchestrator/LICENSE', 'VERSION']:
            (self.root / name).unlink()
        result, value = self.call('check_repository.py')
        self.assertEqual(result.returncode, 1, value)
        self.assertFalse(value['ok'])
        self.assertTrue(any('VERSION' in e for e in value['errors']))

    def test_checker_detects_non_english_text_and_broken_links(self):
        (self.root / 'bad.md').write_text(chr(0x4e2d) + '\n[missing](absent.md)', encoding='utf-8')
        result, value = self.call('check_repository.py')
        self.assertEqual(result.returncode, 1, value)
        self.assertTrue(any('Non-English' in e for e in value['errors']))
        self.assertTrue(any('Broken local link' in e for e in value['errors']))

    def test_standalone_demo_completes_using_only_skill_files(self):
        skill = Path(self.temp.name) / 'standalone'
        shutil.copytree(self.root / 'skills/bot-orchestrator', skill)
        result = subprocess.run([sys.executable, '-B', str(skill / 'scripts/demo.py')],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.addCleanup(shutil.rmtree, value['workspace'])
        self.assertEqual(value['goalStatus'], 'done')
        self.assertTrue((Path(value['workspace']) / 'summary.md').is_file())


if __name__ == '__main__':
    unittest.main(verbosity=2)

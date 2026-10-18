#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Copy the complete skill without overwriting an existing installation."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, help='Full path to the new skill directory.')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    source = repo / 'skills' / 'bot-orchestrator'
    home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex').expanduser()
    target = (args.destination or home / 'skills' / 'bot-orchestrator').expanduser().absolute()
    if target.exists() or target.is_symlink():
        print(json.dumps({'ok': False, 'error': 'DESTINATION_EXISTS',
                          'message': 'Inspect or back up the existing directory; it was not changed.'}))
        return 2
    resolved_target = target.resolve()
    if resolved_target == source or source in resolved_target.parents:
        print(json.dumps({'ok': False, 'error': 'DESTINATION_INSIDE_SOURCE',
                          'message': 'Choose an installation directory outside the source skill directory.'}))
        return 2
    if not (source / 'SKILL.md').is_file() or not (source / 'LICENSE').is_file():
        print(json.dumps({'ok': False, 'error': 'INCOMPLETE_SOURCE'}))
        return 2
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
    except OSError:
        print(json.dumps({'ok': False, 'error': 'COPY_FAILED',
                          'message': 'Installation was not confirmed; inspect the destination for a partial copy.'}))
        return 2
    print(json.dumps({'ok': True, 'installedPath': str(target),
                      'next': 'Refresh host skill discovery or start a new session.'}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())

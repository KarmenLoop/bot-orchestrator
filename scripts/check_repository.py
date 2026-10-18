#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check publication content without network access or third-party packages."""
import ast
import json
from pathlib import Path
import re
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    skill = root / 'skills' / 'bot-orchestrator'
    required = ['README.md', 'LICENSE', 'NOTICE', 'VERSION', 'CONTRIBUTING.md',
                'SECURITY.md', 'SUPPORT.md', 'CODE_OF_CONDUCT.md', 'CHANGELOG.md',
                'skills/bot-orchestrator/SKILL.md', 'skills/bot-orchestrator/LICENSE',
                'skills/bot-orchestrator/agents/openai.yaml', 'examples/local_demo.py',
                'skills/bot-orchestrator/scripts/demo.py', 'scripts/test_repository.py', 'scripts/validate.py',
                'skills/bot-orchestrator/scripts/moa.py', 'skills/bot-orchestrator/scripts/test_moa.py',
                'skills/bot-orchestrator/scripts/moa_demo.py', 'skills/bot-orchestrator/scripts/moa_demo_adapter.py',
                'skills/bot-orchestrator/references/moa.md', 'skills/bot-orchestrator/references/orchestration.md',
                'examples/moa_demo.py']
    errors = [f'Missing required file: {name}' for name in required if not (root / name).is_file()]
    files = [p for p in root.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts]
    for file in files:
        if file.suffix not in ('.md', '.py', '.yaml', '.yml', '.txt') and file.name not in ('LICENSE', 'NOTICE', 'VERSION', '.gitignore'):
            errors.append(f'Unexpected publication file: {file.relative_to(root)}')
            continue
        content = file.read_text(encoding='utf-8')
        if re.search(r'[\u3400-\u9fff]', content):
            errors.append(f'Non-English publication text: {file.relative_to(root)}')
        if re.search(r'/(?:Users|home)/[A-Za-z0-9._-]+/|[A-Z]:\\Users\\', content):
            errors.append(f'Machine-specific user path: {file.relative_to(root)}')
        if re.search(r'\[(?:TODO|TBD):', content):
            errors.append(f'Unfinished scaffold: {file.relative_to(root)}')
        if file.suffix == '.py':
            try:
                ast.parse(content, filename=str(file), feature_version=(3, 9))
            except SyntaxError as error:
                errors.append(f'Python 3.9 syntax: {file.relative_to(root)}: {error.msg}')
        if file.suffix == '.md':
            for target in re.findall(r'\]\(([^)]+)\)', content):
                if '://' in target or target.startswith(('mailto:', '#')):
                    continue
                relative = target.split('#', 1)[0]
                if relative and not (file.parent / relative).resolve().is_file():
                    errors.append(f'Broken local link: {file.relative_to(root)} -> {target}')
    entry_file, version_file = skill / 'SKILL.md', root / 'VERSION'
    if entry_file.is_file():
        entry = entry_file.read_text(encoding='utf-8')
        if not entry.startswith('---\n') or 'name: bot-orchestrator\n' not in entry.split('---', 2)[1]:
            errors.append('Skill identity/frontmatter missing')
        if version_file.is_file() and 'version: "' + version_file.read_text().strip() + '"' not in entry:
            errors.append('Skill and repository versions differ')
    root_license, skill_license = root / 'LICENSE', skill / 'LICENSE'
    if root_license.is_file() and skill_license.is_file() and root_license.read_bytes() != skill_license.read_bytes():
        errors.append('Standalone skill license differs from repository license')
    print(json.dumps({'ok': not errors, 'filesChecked': len(files), 'errors': errors}, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())

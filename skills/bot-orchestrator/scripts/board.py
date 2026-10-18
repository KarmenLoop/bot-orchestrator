#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Local orchestration records. Never executes commands or external actions."""
import argparse
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import sys

MAX_FILE = 64 * 1024 * 1024


class BoardError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message


def require(condition, code, message):
    if not condition:
        raise BoardError(code, message)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def timestamp(value):
    try:
        result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(result.tzinfo is not None, 'TIMEZONE_REQUIRED', 'Use an ISO time with UTC offset.')
        return result.astimezone(dt.timezone.utc)
    except (ValueError, AttributeError):
        raise BoardError('INVALID_TIME', 'Use an ISO time with UTC offset.')


def relative(root, value):
    p = PurePosixPath(value)
    require(bool(value) and not p.is_absolute() and '..' not in p.parts
            and '\\' not in value and ':' not in value,
            'INVALID_PATH', 'Use a workspace-relative path without parent traversal.')
    target = (root / value).resolve()
    require(target == root or root in target.parents, 'OUTSIDE_WORKSPACE', 'Path leaves the workspace.')
    return target.relative_to(root).as_posix()


def pin(root, value):
    # Resolve at use time as well as declaration time; do not follow a new escape.
    rel = relative(root, value)
    file = root / rel
    require(not (root / value).is_symlink(), 'SYMLINK_EVIDENCE', 'Evidence must be a regular file.')
    try:
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0)
        with os.fdopen(os.open(file, flags), 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_FILE,
                    'INVALID_EVIDENCE', 'Evidence must be a regular file no larger than 64 MiB.')
            digest, size = hashlib.sha256(), 0
            while True:
                part = stream.read(1024 * 1024)
                if not part:
                    break
                size += len(part)
                require(size <= MAX_FILE, 'INVALID_EVIDENCE', 'Evidence exceeded 64 MiB.')
                digest.update(part)
            after = os.fstat(stream.fileno())
        require((before.st_ino, before.st_size, before.st_mtime_ns) ==
                (after.st_ino, after.st_size, after.st_mtime_ns),
                'EVIDENCE_CHANGED', 'File changed while reading it.')
    except OSError:
        raise BoardError('EVIDENCE_UNREADABLE', 'Evidence file is missing or unreadable.')
    return {'path': rel, 'bytes': size, 'sha256': digest.hexdigest()}


def changed(root, records, cache=None):
    cache = {} if cache is None else cache
    result = []
    for record in records:
        try:
            if record['path'] not in cache:
                cache[record['path']] = pin(root, record['path'])
        except BoardError:
            cache[record['path']] = None
        if cache[record['path']] != record:
            result.append(record['path'])
    return result


def task_records(task):
    records = list((task.get('submission') or {}).get('files', []))
    if task.get('reviews') and task['reviews'][-1]['decision'] == 'accept':
        records += task['reviews'][-1]['files']
    return records


def task_of(state, key):
    require(key in state['tasks'], 'TASK_NOT_FOUND', 'Task does not exist.')
    return state['tasks'][key]


def dependencies(state, task, root, cache=None):
    # Iterative traversal also supports chains deeper than Python's call stack.
    pending, visited = list(reversed(task['depends'])), set()
    cache = {} if cache is None else cache
    while pending:
        dep = pending.pop()
        if dep in visited:
            continue
        visited.add(dep)
        upstream = task_of(state, dep)
        require(upstream['status'] == 'done', 'DEPENDENCY_PENDING', 'Dependency is not accepted: ' + dep)
        require(not changed(root, task_records(upstream), cache),
                'DEPENDENCY_CHANGED', 'Accepted dependency evidence changed: ' + dep)
        pending.extend(reversed(upstream['depends']))


def preflight(state, task, root, cache=None):
    require(task['status'] == 'pending', 'INVALID_TRANSITION', 'Only pending tasks can start.')
    dependencies(state, task, root, cache)
    require(task['attempts'] < task['maxAttempts'], 'ATTEMPT_BUDGET',
            'Attempt budget exhausted; replan instead of looping.')
    for other in state['tasks'].values():
        if other['id'] != task['id'] and other['status'] in ('running', 'review'):
            require(not any(overlap(a, b) for a in task['writes'] for b in other['writes']),
                    'WRITE_CONFLICT', 'Overlapping declared write scope held by: ' + other['id'])


def overlap(left, right):
    return left == '.' or right == '.' or left == right or left.startswith(right + '/') or right.startswith(left + '/')


def invalidate(state, key):
    affected = {key}
    while True:
        extra = {tid for tid, task in state['tasks'].items()
                 if tid not in affected and set(task['depends']) & affected}
        if not extra:
            break
        affected.update(extra)
    for tid in affected - {key}:
        task = state['tasks'][tid]
        if task['status'] != 'cancelled':
            task['status'] = 'blocked'
            task['reason'] = 'Upstream task changed: ' + key
            task['wakeAt'] = None
    return sorted(affected - {key})


def inspect(state, root, cache=None):
    cache = {} if cache is None else cache
    issues = []
    for tid, task in state['tasks'].items():
        if task['status'] == 'cancelled':
            continue
        for path in changed(root, task_records(task), cache):
            issues.append({'task': tid, 'path': path, 'code': 'EVIDENCE_CHANGED'})
    for path in changed(root, (state.get('closure') or {}).get('files', []), cache):
        issues.append({'task': None, 'path': path, 'code': 'CLOSURE_CHANGED'})
    return issues


def next_actions(state, root, moment, limit=2):
    require(type(limit) is int and 1 <= limit <= 16, 'INVALID_LIMIT', 'Batch limit must be between 1 and 16.')
    cache = {}
    issues = inspect(state, root, cache)
    result = {'goal': state['goal'], 'boardStatus': state['status'], 'revision': state['revision'],
              'ready': [], 'blocked': [], 'inFlight': [], 'waiting': [], 'evidenceIssues': issues}
    for tid, task in state['tasks'].items():
        status = task['status']
        if status == 'pending' and state['status'] == 'open':
            try:
                preflight(state, task, root, cache)
                result['ready'].append(tid)
            except BoardError as error:
                result['blocked'].append({'task': tid, 'code': error.code, 'reason': error.message})
        elif status in ('running', 'review'):
            result['inFlight'].append({'task': tid, 'status': status, 'owner': task['owner']})
        elif status == 'waiting':
            result['waiting'].append({'task': tid, 'reason': task['reason'], 'wakeAt': task['wakeAt'],
                                      'due': bool(task['wakeAt'] and timestamp(task['wakeAt']) <= moment)})
        elif status == 'blocked':
            result['blocked'].append({'task': tid, 'code': 'TASK_BLOCKED', 'reason': task['reason']})
    children = {tid: [] for tid in state['tasks']}
    for tid, task in state['tasks'].items():
        for dep in task['depends']:
            children[dep].append(tid)
    scores = {}
    for tid in result['ready']:
        pending, consumers = [tid], set()
        while pending:
            key = pending.pop()
            if key not in consumers:
                consumers.add(key); pending.extend(children[key])
        scores[tid] = sum(state['tasks'][key]['required'] and state['tasks'][key]['status'] != 'done' for key in consumers)
    result['rankedReady'] = sorted(result['ready'], key=lambda tid: -scores[tid])
    result['requiredWorkReachable'] = scores
    result['recommendedBatch'] = []
    selected_writes = []
    for tid in result['rankedReady']:
        writes = state['tasks'][tid]['writes']
        if not any(overlap(a, b) for a in writes for b in selected_writes):
            result['recommendedBatch'].append(tid); selected_writes.extend(writes)
            if len(result['recommendedBatch']) == limit:
                break
    settled = bool(state['tasks']) and all(t['status'] in ('done', 'cancelled') for t in state['tasks'].values())
    result['goalAction'] = ('inspect_closed_goal' if state['status'] == 'done' else
                            'inspect_changed_evidence' if issues else
                            'review_goal_acceptance' if settled else 'continue')
    result['note'] = 'Read-only snapshot. Start rechecks readiness; reminders do not resume tasks or prove process liveness.'
    return result


def validate_state(state):
    """Reject malformed current state before any command; never repair it implicitly."""
    def valid(condition):
        require(condition, 'INVALID_BOARD_STATE', 'Malformed board state; preserve the database and inspect a backup.')

    def text(value):
        return isinstance(value, str) and bool(value.strip())

    def path(value):
        return (text(value) and not PurePosixPath(value).is_absolute() and
                '..' not in PurePosixPath(value).parts and '\\' not in value and ':' not in value)

    def paths(values):
        return isinstance(values, list) and bool(values) and all(path(p) for p in values)

    def files(records):
        valid(isinstance(records, list) and bool(records))
        for record in records:
            valid(isinstance(record, dict) and path(record.get('path')) and
                  type(record.get('bytes')) is int and 0 <= record['bytes'] <= MAX_FILE and
                  isinstance(record.get('sha256'), str) and
                  re.fullmatch(r'[0-9a-f]{64}', record['sha256']) is not None)

    def dated(value):
        valid(text(value))
        try:
            timestamp(value)
        except BoardError:
            valid(False)

    valid(isinstance(state, dict))
    require(type(state.get('schemaVersion')) is int and state['schemaVersion'] == 1,
            'UNSUPPORTED_SCHEMA', 'Unsupported board schema.')
    valid(text(state.get('workspace')) and Path(state['workspace']).is_absolute())
    valid(text(state.get('goal')) and text(state.get('acceptance')) and state.get('status') in ('open', 'done'))
    valid(type(state.get('revision')) is int and state['revision'] >= 1)
    valid(isinstance(state.get('events'), list) and isinstance(state.get('tasks'), dict) and len(state['tasks']) <= 1000)
    for key, task in state['tasks'].items():
        valid(isinstance(task, dict) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', key) is not None)
        valid(task.get('id') == key and all(text(task.get(k)) for k in ('objective', 'acceptance', 'owner')))
        valid(task.get('status') in ('pending', 'running', 'review', 'waiting', 'blocked', 'done', 'cancelled'))
        valid(paths(task.get('deliverables')) and paths(task.get('writes')))
        valid(isinstance(task.get('depends'), list) and all(isinstance(d, str) and d in state['tasks'] for d in task['depends']))
        valid(type(task.get('required')) is bool and type(task.get('maxAttempts')) is int and 1 <= task['maxAttempts'] <= 20)
        valid(type(task.get('attempts')) is int and 0 <= task['attempts'] <= task['maxAttempts'])
        valid(isinstance(task.get('reason'), str) and 'wakeAt' in task)
        if task['wakeAt'] is not None:
            valid(task['status'] == 'waiting'); dated(task['wakeAt'])
        valid('submission' in task and isinstance(task.get('reviews'), list) and isinstance(task.get('previous'), list))
        if task['submission'] is not None:
            valid(isinstance(task['submission'], dict) and text(task['submission'].get('note')))
            files(task['submission'].get('files')); dated(task['submission'].get('at'))
            valid(set(task['deliverables']).issubset({r['path'] for r in task['submission']['files']}))
        for review in task['reviews']:
            valid(isinstance(review, dict) and review.get('decision') in ('accept', 'rework') and
                  text(review.get('reason')) and text(review.get('reviewer')))
            files(review.get('files')); dated(review.get('at'))
        if task['status'] in ('review', 'done'):
            valid(task['submission'] is not None and task['attempts'] > 0)
        if task['status'] == 'done':
            valid(bool(task['reviews']) and task['reviews'][-1]['decision'] == 'accept')
    # Kahn's algorithm detects tampered cycles without recursion or filesystem work.
    remaining = {key: set(task['depends']) for key, task in state['tasks'].items()}
    children = {key: [] for key in remaining}
    for key, parents in remaining.items():
        for parent in parents:
            children[parent].append(key)
    ready = [key for key, parents in remaining.items() if not parents]
    seen = 0
    while ready:
        key = ready.pop(); seen += 1
        for child in children[key]:
            remaining[child].remove(key)
            if not remaining[child]:
                ready.append(child)
    valid(seen == len(remaining))
    valid('closure' in state)
    if state['closure'] is not None:
        valid(isinstance(state['closure'], dict) and text(state['closure'].get('reason')))
        files(state['closure'].get('files')); dated(state['closure'].get('at'))
    if state['status'] == 'done':
        required = [t for t in state['tasks'].values() if t['required']]
        valid(state['closure'] is not None and bool(required) and all(t['status'] == 'done' for t in required))
        valid(all(t['status'] in ('done', 'cancelled') for t in state['tasks'].values()))


def event(state, action, task=None, note=''):
    state['revision'] += 1
    state['events'].append({'revision': state['revision'], 'at': now(),
                            'action': action, 'task': task, 'note': note})


def execute(state, args):
    root = Path(state['workspace'])
    command = args.command
    for field in ('objective', 'check', 'owner', 'reason', 'note', 'reviewer'):
        if hasattr(args, field):
            require(bool(getattr(args, field).strip()), 'EMPTY_FIELD', 'Required text fields must not be empty.')
    if command in ('status', 'due', 'verify', 'next'):
        if command == 'next':
            moment = timestamp(args.now) if args.now else timestamp(now())
            return next_actions(state, root, moment, args.limit), 0
        if command == 'verify':
            issues = inspect(state, root)
            return {'ok': not issues, 'issues': issues}, bool(issues)
        if command == 'due':
            moment = timestamp(args.now) if args.now else timestamp(now())
            return {'due': [tid for tid, task in state['tasks'].items()
                            if task['status'] == 'waiting' and task.get('wakeAt')
                            and timestamp(task['wakeAt']) <= moment],
                    'note': 'Due is a reminder to inspect the condition; no scheduler or automatic resume.'}, 0
        if args.full:
            return state, 0
        return {'goal': state['goal'], 'acceptance': state['acceptance'],
                'status': state['status'], 'revision': state['revision'],
                'tasks': [{k: t[k] for k in ('id', 'objective', 'status', 'owner', 'depends', 'attempts', 'reason', 'wakeAt')}
                          for t in state['tasks'].values()],
                'readyByDependency': [tid for tid, t in state['tasks'].items() if t['status'] == 'pending'
                                      and all(state['tasks'][d]['status'] == 'done' for d in t['depends'])]}, 0

    require(state['status'] == 'open' or command == 'reopen', 'BOARD_CLOSED', 'Reopen an accepted task before changing a closed board.')
    task = None
    if command == 'add':
        require(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', args.task) is not None,
                'INVALID_TASK_ID', 'Task id must be 1-64 letters, numbers, underscores or hyphens.')
        require(args.task not in state['tasks'], 'TASK_EXISTS', 'Task already exists.')
        require(len(state['tasks']) < 1000, 'TASK_LIMIT', 'Use a separate board for additional tasks.')
        require(1 <= args.max_attempts <= 20, 'INVALID_BUDGET', 'max-attempts must be between 1 and 20.')
        # Dependencies must already exist. Append-only edges make cycles impossible.
        require(all(dep in state['tasks'] for dep in args.depends), 'UNKNOWN_DEPENDENCY', 'Add dependencies before dependants.')
        deliverables = list(dict.fromkeys(relative(root, p) for p in args.deliverable))
        writes = list(dict.fromkeys(relative(root, p) for p in (args.write or args.deliverable)))
        task = {'id': args.task, 'objective': args.objective, 'acceptance': args.check,
                'deliverables': deliverables, 'writes': writes, 'depends': list(dict.fromkeys(args.depends)),
                'owner': args.owner, 'required': not args.optional, 'status': 'pending',
                'attempts': 0, 'maxAttempts': args.max_attempts, 'reason': '', 'wakeAt': None,
                'submission': None, 'reviews': [], 'previous': []}
        state['tasks'][args.task] = task
    elif command == 'close':
        required = [t for t in state['tasks'].values() if t['required']]
        require(required and all(t['status'] == 'done' for t in required),
                'REQUIRED_WORK_OPEN', 'Every required task must be accepted; cancellation does not satisfy it.')
        require(all(t['status'] in ('done', 'cancelled') for t in state['tasks'].values()),
                'WORK_ACTIVE', 'Close or cancel optional work before closing the board.')
        require(not inspect(state, root), 'EVIDENCE_CHANGED', 'Evidence changed; review it again.')
        state['closure'] = {'files': [pin(root, p) for p in args.evidence], 'reason': args.reason, 'at': now()}
        state['status'] = 'done'
    else:
        task = task_of(state, args.task)
        status = task['status']
        if command == 'start':
            preflight(state, task, root)
            task['status'], task['attempts'], task['reason'] = 'running', task['attempts'] + 1, ''
        elif command == 'submit':
            require(status == 'running', 'INVALID_TRANSITION', 'Only running tasks can submit.')
            dependencies(state, task, root)
            files = list(dict.fromkeys(task['deliverables'] + args.evidence))
            task['submission'] = {'files': [pin(root, p) for p in files], 'note': args.note, 'at': now()}
            task['status'] = 'review'
        elif command == 'review':
            require(status == 'review', 'INVALID_TRANSITION', 'Only submitted tasks can be reviewed.')
            files = [pin(root, p) for p in args.evidence]
            if args.decision == 'accept':
                dependencies(state, task, root)
                require(not changed(root, task['submission']['files']), 'EVIDENCE_CHANGED', 'Submitted files changed before acceptance.')
            review = {'decision': args.decision, 'reviewer': args.reviewer,
                      'reason': args.reason, 'files': files, 'at': now()}
            task['reviews'].append(review)
            task['status'] = 'done' if args.decision == 'accept' else 'pending'
            task['reason'] = args.reason
        elif command == 'mark':
            require(status not in ('done', 'cancelled'), 'INVALID_TRANSITION', 'Reopen accepted work; cancelled work needs explicit resume.')
            require(args.state == 'waiting' or not args.wake_at, 'INVALID_WAKE', 'wake-at only applies to waiting.')
            task['status'], task['reason'] = args.state, args.reason
            task['wakeAt'] = timestamp(args.wake_at).isoformat() if args.wake_at else None
            if args.state == 'cancelled':
                invalidate(state, task['id'])
        elif command == 'resume':
            require(status in ('waiting', 'blocked', 'cancelled'), 'INVALID_TRANSITION', 'Task is not waiting, blocked or cancelled.')
            dependencies(state, task, root)
            task['status'], task['reason'], task['wakeAt'] = 'pending', args.reason, None
        elif command == 'reopen':
            require(status == 'done', 'INVALID_TRANSITION', 'Only accepted tasks can be reopened.')
            task['previous'].append({'submission': copy.deepcopy(task['submission']), 'reviews': copy.deepcopy(task['reviews'])})
            task['submission'], task['reviews'] = None, []
            task['status'], task['reason'] = 'pending', args.reason
            invalidate(state, task['id'])
            state['status'], state['closure'] = 'open', None
    event(state, command, task['id'] if task else None, getattr(args, 'reason', '') or getattr(args, 'note', ''))
    return {'ok': True, 'revision': state['revision'], 'task': task, 'status': state['status']}, 0


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db', required=True, help='Explicit path to this goal\'s SQLite board.')
    sub = p.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init'); init.add_argument('--workspace', required=True)
    init.add_argument('--goal', required=True); init.add_argument('--acceptance', required=True)
    add = sub.add_parser('add'); add.add_argument('task'); add.add_argument('--objective', required=True)
    add.add_argument('--check', required=True); add.add_argument('--deliverable', action='append', required=True)
    add.add_argument('--depends', action='append', default=[]); add.add_argument('--write', action='append', default=[])
    add.add_argument('--owner', default='current-agent'); add.add_argument('--max-attempts', type=int, default=3)
    add.add_argument('--optional', action='store_true')
    sub.add_parser('status').add_argument('--full', action='store_true')
    sub.add_parser('verify')
    for command in ('due', 'next'):
        query = sub.add_parser(command)
        query.add_argument('--now', help='ISO offset time; omit to use current UTC.')
        if command == 'next':
            query.add_argument('--limit', type=int, default=2, help='Advisory disjoint batch size, 1-16.')
    sub.add_parser('start').add_argument('task')
    submit = sub.add_parser('submit'); submit.add_argument('task')
    submit.add_argument('--evidence', action='append', required=True); submit.add_argument('--note', required=True)
    review = sub.add_parser('review'); review.add_argument('task')
    review.add_argument('--decision', choices=('accept', 'rework'), required=True)
    review.add_argument('--evidence', action='append', required=True); review.add_argument('--reason', required=True)
    review.add_argument('--reviewer', default='self')
    mark = sub.add_parser('mark'); mark.add_argument('task')
    mark.add_argument('--state', choices=('waiting', 'blocked', 'cancelled'), required=True)
    mark.add_argument('--reason', required=True); mark.add_argument('--wake-at')
    for command in ('resume', 'reopen'):
        item = sub.add_parser(command); item.add_argument('task'); item.add_argument('--reason', required=True)
    close = sub.add_parser('close'); close.add_argument('--evidence', action='append', required=True)
    close.add_argument('--reason', required=True)
    return p


def run(args):
    db = Path(args.db).expanduser().absolute()
    require(not db.is_symlink(), 'INVALID_DATABASE', 'Database must not be a symlink.')
    if args.command == 'init':
        root = Path(args.workspace).expanduser().resolve()
        require(root.is_dir(), 'INVALID_WORKSPACE', 'Workspace must already exist.')
        require(args.goal.strip() and args.acceptance.strip(), 'EMPTY_GOAL', 'Goal and acceptance must not be empty.')
        db.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(db, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        except FileExistsError:
            raise BoardError('BOARD_EXISTS', 'Existing board is never overwritten by init.')
        state = {'schemaVersion': 1, 'workspace': str(root), 'goal': args.goal,
                 'acceptance': args.acceptance, 'status': 'open', 'revision': 0,
                 'tasks': {}, 'events': [], 'closure': None}
        event(state, 'init')
        with sqlite3.connect(str(db), timeout=5) as conn:
            conn.execute('CREATE TABLE board (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
            conn.execute('INSERT INTO board VALUES(1,?)', (json.dumps(state, ensure_ascii=False),))
        return {'ok': True, 'db': str(db), 'workspace': str(root)}, 0
    require(db.is_file(), 'BOARD_NOT_FOUND', 'Initialize an explicit board first.')
    readonly = args.command in ('status', 'due', 'verify', 'next')
    with sqlite3.connect(db.as_uri() + ('?mode=ro' if readonly else '?mode=rw'), uri=True, timeout=5) as conn:
        if not readonly:
            conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT payload FROM board WHERE id=1').fetchone()
        require(row is not None, 'INVALID_DATABASE', 'Board state is missing.')
        state = json.loads(row[0])
        validate_state(state)
        result, code = execute(state, args)
        if not readonly:
            conn.execute('UPDATE board SET payload=? WHERE id=1', (json.dumps(state, ensure_ascii=False),))
    return result, code


def main():
    try:
        result, code = run(parser().parse_args())
    except BoardError as error:
        result, code = {'ok': False, 'error': {'code': error.code, 'message': error.message}}, 2
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError):
        result, code = {'ok': False, 'error': {'code': 'BOARD_IO_OR_FORMAT', 'message': 'Board I/O or format error; no successful transition confirmed.'}}, 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(main())

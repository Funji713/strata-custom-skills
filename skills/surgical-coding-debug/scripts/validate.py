#!/usr/bin/env python3
"""Offline package, receipt and state-gate lint; never runs inspected commands.

The YAML reader supports only this package's one/two-level scalar mappings.
This is not a general YAML/Markdown parser, an evidence verifier or a model eval.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

NAMES = {'surgical-coding-debug', 'project-architecture-workflow'}
VERSION = '1.0.0'
TRANSITIONS = {
    'planned': {'in_progress', 'blocked', 'superseded'},
    'in_progress': {'verified', 'blocked', 'needs_revalidation', 'superseded'},
    'blocked': {'planned', 'in_progress', 'needs_revalidation', 'superseded'},
    'verified': {'needs_revalidation', 'superseded'},
    'needs_revalidation': {'in_progress', 'blocked', 'verified', 'superseded'},
    'superseded': set(),
}
COMMON = ('references/execution-protocol.md', 'scripts/validate.py',
          'tests/test_validate.py', 'evals/README.md')


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def strict_json(text: str) -> object:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result

    def constant(value):
        raise ValueError(f'non-finite JSON constant: {value}')

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def mapping(text: str) -> dict:
    """Parse the deliberately restricted YAML used by this package's metadata."""
    result: dict = {}
    current = None
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.fullmatch(r'( {0}| {2})([a-z_]+):(?: (.*))?', line)
        if not match:
            raise ValueError(f'unsupported YAML syntax at line {number}')
        indent, key, value = match.groups()
        if indent:
            if current is None:
                raise ValueError(f'child without mapping at line {number}')
            target = current
        else:
            target, current = result, None
        if key in target:
            raise ValueError(f'duplicate YAML key: {key}')
        if value is None:
            if indent:
                raise ValueError('mappings deeper than two levels are unsupported')
            target[key] = {}
            current = target[key]
        elif value.startswith('"'):
            target[key] = strict_json(value)
            if not isinstance(target[key], str):
                raise ValueError('expected quoted string')
        elif value in ('true', 'false'):
            target[key] = value == 'true'
        elif re.fullmatch(r'[a-z0-9-]+', value):
            target[key] = value
        else:
            raise ValueError(f'quote scalar value for {key}')
    return result


def metadata(text: str) -> dict:
    match = re.match(r'\A---\n(.*?)\n---\n', text, re.S)
    if not match:
        raise ValueError('missing YAML frontmatter')
    return mapping(match.group(1))


def receipt_errors(receipt: object) -> list[str]:
    """Check declared consistency only; observations/artifacts need real review."""
    fields = {'criteria', 'spec_revision', 'snapshot', 'environment',
              'dependencies_verified', 'unresolved_deviations', 'checks'}
    if not isinstance(receipt, dict):
        return ['receipt must be an object']
    errors = []
    if set(receipt) != fields:
        errors.append('unexpected or missing receipt fields')
    criteria = receipt.get('criteria')
    if (not isinstance(criteria, list) or not criteria
            or not all(nonempty(c) for c in criteria) or len(set(criteria)) != len(criteria)):
        return errors + ['criteria must be a nonempty list of unique strings']
    for key in ('spec_revision', 'snapshot', 'environment'):
        if not nonempty(receipt.get(key)):
            errors.append(f'missing {key}')
    if receipt.get('dependencies_verified') is not True:
        errors.append('dependencies are not verified')
    if receipt.get('unresolved_deviations') != []:
        errors.append('deviations must be explicitly resolved')
    checks = receipt.get('checks')
    if not isinstance(checks, list) or not checks:
        return errors + ['checks must be nonempty']
    covered = set()
    for index, check in enumerate(checks):
        prefix = f'check[{index}]'
        if not isinstance(check, dict):
            errors.append(f'{prefix} must be an object')
            continue
        required = {'criterion', 'kind', 'outcome', 'executed', 'procedure',
                    'expected', 'observed', 'artifact', 'spec_revision', 'snapshot'}
        if check.get('kind') == 'test':
            required.add('count')
        if set(check) != required:
            errors.append(f'{prefix} has unexpected or missing fields')
        criterion = check.get('criterion')
        if not isinstance(criterion, str) or criterion not in criteria:
            errors.append(f'{prefix} has unknown criterion')
        else:
            covered.add(criterion)
        if check.get('outcome') != 'passed' or check.get('executed') is not True:
            errors.append(f'{prefix} did not execute and pass')
        kind = check.get('kind')
        if kind not in ('test', 'build', 'lint', 'manual'):
            errors.append(f'{prefix} has unknown check kind')
        if kind == 'test' and (type(check.get('count')) is not int or check['count'] <= 0):
            errors.append(f'{prefix} has no executed tests')
        for key in ('procedure', 'expected', 'observed', 'artifact'):
            if not nonempty(check.get(key)):
                errors.append(f'{prefix} missing {key}')
        for key in ('snapshot', 'spec_revision'):
            if not nonempty(check.get(key)) or check.get(key) != receipt.get(key):
                errors.append(f'{prefix} stale or missing {key}')
    if covered != set(criteria):
        errors.append('acceptance criteria lack evidence')
    return errors


def transition_errors(before: str, after: str, receipt: object = None,
                      reason: str | None = None) -> list[str]:
    if (not isinstance(before, str) or not isinstance(after, str)
            or after not in TRANSITIONS.get(before, set())):
        return [f'illegal state transition: {before} -> {after}']
    errors = []
    if (before == 'blocked' or after in {'blocked', 'needs_revalidation', 'superseded'}) and not nonempty(reason):
        errors.append('transition needs a blocker/resolution/invalidation/replacement reason')
    if after == 'verified':
        errors.extend(receipt_errors(receipt))
    return errors


def validate(root: Path, peer: Path | None = None) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    required = ('SKILL.md', 'README.md', 'agents/openai.yaml', 'evals/cases.json',
                '.github/workflows/validate.yml', 'CHANGELOG.md', *COMMON)
    for name in required:
        if not (root / name).is_file():
            errors.append(f'missing file: {name}')
    if errors:
        return errors
    try:
        skill = (root / 'SKILL.md').read_text(encoding='utf-8')
        meta = metadata(skill)
        if set(meta) != {'name', 'description'} or not isinstance(meta.get('name'), str) or meta['name'] not in NAMES:
            raise ValueError('invalid skill name/frontmatter fields')
        if not nonempty(meta['description']) or len(meta['description']) > 1024:
            raise ValueError('description must contain 1-1024 characters')
        # Project budget, not an asserted host limit.
        if len(skill.splitlines()) > 200 or len(skill.encode('utf-8')) > 10000:
            errors.append('SKILL.md exceeds the local entry-point budget')
        if 'references/execution-protocol.md' not in skill:
            errors.append('entry point does not link to the execution protocol')
        agent = mapping((root / 'agents/openai.yaml').read_text(encoding='utf-8'))
        interface = agent.get('interface')
        if not isinstance(interface, dict) or set(interface) != {'display_name', 'short_description', 'default_prompt'}:
            raise ValueError('unexpected interface metadata')
        if not all(nonempty(v) for v in interface.values()):
            raise ValueError('interface strings must be nonempty')
        if '$' + meta['name'] not in interface['default_prompt']:
            errors.append('default_prompt names the wrong skill')
        if agent.get('policy') != {'allow_implicit_invocation': True} or set(agent) != {'interface', 'policy'}:
            errors.append('unexpected invocation policy or agent metadata')
        protocol = (root / COMMON[0]).read_text(encoding='utf-8')
        if protocol.count('Protocol-Version: ' + VERSION) != 1:
            errors.append('missing or inconsistent protocol version')
        if meta['name'] == 'project-architecture-workflow' and not (root / 'references/architecture-control-template.md').is_file():
            errors.append('missing architecture template')
        for document in root.rglob('*.md'):
            if any(part.startswith('.') for part in document.relative_to(root).parts):
                continue
            if not document.resolve().is_relative_to(root):
                errors.append('documentation resolves outside the package')
                continue
            for target in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)', document.read_text(encoding='utf-8')):
                parts = urlsplit(target)
                if parts.scheme or parts.netloc or not parts.path:
                    continue
                destination = (document.parent / unquote(parts.path)).resolve()
                if not destination.is_relative_to(root) or not destination.is_file():
                    errors.append(f'broken/escaping link in {document.relative_to(root)}: {target}')
        cases = strict_json((root / 'evals/cases.json').read_text(encoding='utf-8'))
        if not isinstance(cases, dict) or set(cases) != {'schema_version', 'behavioral_status', 'cases'}:
            raise ValueError('invalid scenario document fields')
        if type(cases['schema_version']) is not int or cases['schema_version'] != 1 or cases['behavioral_status'] != 'not_run':
            errors.append('invalid scenario schema/default execution status')
        scenarios = cases['cases']
        if not isinstance(scenarios, list) or len(scenarios) < 10:
            raise ValueError('at least ten scenario specifications are required')
        seen = set()
        for case in scenarios:
            if not isinstance(case, dict) or not nonempty(case.get('id')):
                raise ValueError('scenario must have a nonempty ID')
            if set(case) != {'id', 'setup', 'prompt', 'expected', 'must', 'must_not'}:
                errors.append('unexpected scenario fields')
            if case['id'] in seen:
                errors.append('duplicate scenario ID')
            seen.add(case['id'])
            for key in ('setup', 'prompt'):
                if not nonempty(case.get(key)):
                    errors.append(f'{case["id"]}: missing {key}')
            for key in ('must', 'must_not'):
                values = case.get(key)
                if not isinstance(values, list) or not values or not all(nonempty(v) for v in values):
                    errors.append(f'{case["id"]}: missing {key} assertions')
            expected = case.get('expected')
            domains = {'mode': {'plan', 'review', 'implement', 'debug'},
                       'route': {'architecture', 'implementation'},
                       'lane': {'Fast', 'Deep', 'n/a'}, 'risk': {'R0', 'R1', 'R2'},
                       'state': set(TRANSITIONS)}
            if not isinstance(expected, dict):
                raise ValueError('expected must be an object')
            if set(expected) != set(domains):
                errors.append(f'{case["id"]}: unexpected expectation fields')
            for key, allowed in domains.items():
                if not isinstance(expected.get(key), str) or expected[key] not in allowed:
                    errors.append(f'{case["id"]}: invalid {key}')
        if peer is not None:
            peer = peer.resolve()
            peer_name = metadata((peer / 'SKILL.md').read_text(encoding='utf-8')).get('name')
            if peer == root or not isinstance(peer_name, str) or peer_name not in NAMES or peer_name == meta['name']:
                errors.append('peer must declare the other companion skill')
            for name in COMMON:
                if (root / name).read_text(encoding='utf-8') != (peer / name).read_text(encoding='utf-8'):
                    errors.append(f'peer drift: {name}')
    except (ValueError, TypeError, KeyError, OSError) as exc:
        errors.append(str(exc))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--peer', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--transition', nargs=2, metavar=('FROM', 'TO'))
    parser.add_argument('--reason')
    args = parser.parse_args()
    errors = validate(args.root, args.peer)
    record = None
    if args.receipt is not None:
        try:
            record = strict_json(args.receipt.read_text(encoding='utf-8'))
            errors.extend(receipt_errors(record))
        except (ValueError, OSError) as exc:
            errors.append(f'cannot read receipt: {exc}')
    if args.transition:
        errors.extend(transition_errors(*args.transition, record, args.reason))
    for error in errors:
        print(f'FAIL: {error}', file=sys.stderr)
    if errors:
        return 1
    print('PASS: declared consistency only; evidence truth/model behavior not evaluated.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

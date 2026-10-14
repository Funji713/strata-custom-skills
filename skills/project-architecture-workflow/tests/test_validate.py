"""Offline validator regression tests, not tests of model compliance."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('skill_validate', ROOT / 'scripts/validate.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def receipt():
    return {'criteria': ['AC1'], 'spec_revision': 'spec-1', 'snapshot': 'digest-1',
            'environment': 'isolated fixture', 'dependencies_verified': True,
            'unresolved_deviations': [], 'checks': [
                {'criterion': 'AC1', 'kind': 'test', 'outcome': 'passed',
                 'executed': True, 'count': 1, 'procedure': 'cwd=fixture; run test',
                 'expected': 'lower boundary accepted', 'observed': '1 passed',
                 'artifact': 'fixture-log.txt', 'spec_revision': 'spec-1',
                 'snapshot': 'digest-1'}]}


class ReceiptTests(unittest.TestCase):
    def test_valid_receipt(self):
        self.assertEqual(validator.receipt_errors(receipt()), [])

    def test_non_object(self):
        for value in (None, [], 'passed', 1):
            with self.subTest(value=value):
                self.assertTrue(validator.receipt_errors(value))

    def test_invalid_criteria(self):
        for value in ([], ['AC1', 'AC1'], [None], [{}], 'AC1'):
            data = receipt()
            data['criteria'] = value
            with self.subTest(value=value):
                self.assertTrue(validator.receipt_errors(data))

    def test_missing_coverage(self):
        data = receipt()
        data['criteria'].append('AC2')
        self.assertTrue(validator.receipt_errors(data))

    def test_unexecuted_or_unsuccessful(self):
        for field, values in {'executed': [False, 'true', 1],
                              'outcome': ['skipped', 'blocked', 'cancelled', 'failed', 'not_run']}.items():
            for value in values:
                data = receipt()
                data['checks'][0][field] = value
                with self.subTest(field=field, value=value):
                    self.assertTrue(validator.receipt_errors(data))

    def test_no_executed_tests(self):
        for value in (0, -1, True, '1', None):
            data = receipt()
            data['checks'][0]['count'] = value
            with self.subTest(value=value):
                self.assertTrue(validator.receipt_errors(data))

    def test_stale_snapshot_or_spec(self):
        for field in ('snapshot', 'spec_revision'):
            data = receipt()
            data['checks'][0][field] = 'old'
            self.assertTrue(validator.receipt_errors(data))

    def test_missing_evidence_fields(self):
        for field in ('procedure', 'expected', 'observed', 'artifact'):
            data = receipt()
            del data['checks'][0][field]
            self.assertTrue(validator.receipt_errors(data))

    def test_unresolved_dependencies_or_deviations(self):
        for field, value in [('dependencies_verified', False), ('unresolved_deviations', ['D1'])]:
            data = receipt()
            data[field] = value
            self.assertTrue(validator.receipt_errors(data))

    def test_unknown_check(self):
        for field, value in [('criterion', 'unknown'), ('criterion', []), ('kind', 'guess')]:
            data = receipt()
            data['checks'][0][field] = value
            self.assertTrue(validator.receipt_errors(data))

    def test_manual_evidence(self):
        data = receipt()
        data['checks'][0]['kind'] = 'manual'
        del data['checks'][0]['count']
        self.assertEqual(validator.receipt_errors(data), [])

    def test_unknown_fields_rejected(self):
        for target in ('receipt', 'check'):
            data = receipt()
            (data if target == 'receipt' else data['checks'][0])['typo'] = True
            self.assertTrue(validator.receipt_errors(data))

    def test_json_duplicate_and_nonfinite(self):
        for text in ('{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validator.strict_json(text)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'skill'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git', '__pycache__'))

    def tearDown(self):
        self.temp.cleanup()

    def test_current_package(self):
        self.assertEqual(validator.validate(self.root), [])

    def test_missing_file(self):
        (self.root / 'agents/openai.yaml').unlink()
        self.assertTrue(validator.validate(self.root))

    def test_broken_and_escaping_links(self):
        for link in ('missing.md', '../outside.md'):
            path = self.root / 'README.md'
            original = path.read_text(encoding='utf-8')
            path.write_text(original + f'\n[bad]({link})\n', encoding='utf-8')
            self.assertTrue(validator.validate(self.root))
            path.write_text(original, encoding='utf-8')

    def test_frontmatter_and_duplicate_keys(self):
        with self.assertRaises(ValueError):
            validator.mapping('name: one\nname: two')
        (self.root / 'SKILL.md').write_text('# missing frontmatter\n', encoding='utf-8')
        self.assertTrue(validator.validate(self.root))

    def test_yaml_rejects_unsupported_constructs(self):
        for text in ('name: !unsafe value', 'name: &anchor value', ' name: one', 'name: |'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validator.mapping(text)

    def test_wrong_invocation(self):
        path = self.root / 'agents/openai.yaml'
        value = path.read_text(encoding='utf-8')
        for name in validator.NAMES:
            value = value.replace('$' + name, '$wrong-skill')
        path.write_text(value, encoding='utf-8')
        self.assertTrue(validator.validate(self.root))

    def test_duplicate_case_and_unknown_expectation(self):
        path = self.root / 'evals/cases.json'
        original = json.loads(path.read_text(encoding='utf-8'))
        for change in ('duplicate', 'unknown', 'false_pass'):
            data = copy.deepcopy(original)
            if change == 'duplicate':
                data['cases'].append(copy.deepcopy(data['cases'][0]))
            elif change == 'unknown':
                data['cases'][0]['expected']['risk'] = 'safe-ish'
            else:
                data['behavioral_status'] = 'passed'
            path.write_text(json.dumps(data), encoding='utf-8')
            self.assertTrue(validator.validate(self.root))

    def test_peer_drift_and_same_checkout(self):
        peer = Path(self.temp.name) / 'peer'
        shutil.copytree(self.root, peer)
        self.assertTrue(validator.validate(self.root, peer))
        peer_skill = peer / 'SKILL.md'
        text = peer_skill.read_text(encoding='utf-8')
        local = validator.metadata(text)['name']
        other = next(name for name in validator.NAMES if name != local)
        peer_skill.write_text(text.replace(f'name: {local}\n', f'name: {other}\n'), encoding='utf-8')
        self.assertEqual(validator.validate(self.root, peer), [])
        path = peer / 'references/execution-protocol.md'
        path.write_text(path.read_text(encoding='utf-8') + '\ndrift\n', encoding='utf-8')
        self.assertTrue(validator.validate(self.root, peer))
        self.assertTrue(validator.validate(self.root, self.root))

    def test_protocol_version(self):
        path = self.root / 'references/execution-protocol.md'
        path.write_text(path.read_text(encoding='utf-8').replace('Protocol-Version: 1.0.0',
                                                             'Protocol-Version: 2.0.0'), encoding='utf-8')
        self.assertTrue(validator.validate(self.root))

    def test_corrupt_scenario_json(self):
        path = self.root / 'evals/cases.json'
        for text in ('[]', 'null', '{', '{"schema_version":1,"schema_version":2}'):
            path.write_text(text, encoding='utf-8')
            self.assertTrue(validator.validate(self.root))

    def test_entry_budget(self):
        path = self.root / 'SKILL.md'
        path.write_text(path.read_text(encoding='utf-8') + '\n' * 201, encoding='utf-8')
        self.assertTrue(validator.validate(self.root))

    def test_cli_exit_codes(self):
        script = self.root / 'scripts/validate.py'
        valid = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        invalid = subprocess.run([sys.executable, str(script), '--transition', 'planned', 'verified'],
                                 capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 1)
        self.assertIn('illegal state transition', invalid.stderr)


class TransitionTests(unittest.TestCase):
    def test_allowed_transition_requires_fresh_evidence(self):
        self.assertEqual(validator.transition_errors('in_progress', 'verified', receipt()), [])
        data = receipt()
        data['checks'][0]['snapshot'] = 'old'
        self.assertTrue(validator.transition_errors('needs_revalidation', 'verified', data))
        self.assertTrue(validator.transition_errors('in_progress', 'verified'))

    def test_illegal_shortcuts_and_terminal_state(self):
        for before, after in [('planned', 'verified'), ('blocked', 'verified'),
                              ('superseded', 'in_progress'), ('unknown', 'verified')]:
            with self.subTest(before=before, after=after):
                self.assertTrue(validator.transition_errors(before, after, receipt()))

    def test_invalidation_and_blocker_reason(self):
        for before, after in [('verified', 'needs_revalidation'), ('in_progress', 'blocked'),
                              ('blocked', 'in_progress'), ('planned', 'superseded')]:
            with self.subTest(before=before, after=after):
                self.assertTrue(validator.transition_errors(before, after))
                self.assertEqual(validator.transition_errors(before, after, reason='recorded reason/ref'), [])


if __name__ == '__main__':
    unittest.main()

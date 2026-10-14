import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from skills_mcp import Skills, NAMES


class SkillsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.skills = Skills(str(self.root))

    def tearDown(self):
        self.skills.close()
        self.temp.cleanup()

    def test_all_skills_paginate_without_losing_lines(self):
        self.assertEqual(len(self.skills.call('list_skills', {})['skills']), 6)
        for name in NAMES:
            start, seen = 1, []
            while start:
                result = self.skills.call('read_skill', {'skill': name, 'start_line': start})
                self.assertIn('NOT provided', result['adapter'])
                seen.extend(result['content'].splitlines())
                start = result['next_line']
            expected = (ROOT / 'skills' / name / 'SKILL.md').read_text(encoding='utf-8').splitlines()
            self.assertEqual(len(seen), len(expected))
            self.assertEqual([line.split(': ', 1)[1] for line in seen], expected)

    def test_references_and_path_denials(self):
        self.assertIn('content', self.skills.call('read_skill', {'skill': 'surgical-coding-debug', 'path': 'references/execution-protocol.md'}))
        for path in ('../README.md', '/etc/passwd', 'C:\\Users\\x', 'package/../../SKILL.md'):
            with self.assertRaises(ValueError):
                self.skills.call('read_skill', {'skill': 'architecture-visualizer', 'path': path})

    def test_router_is_advisory(self):
        result = self.skills.call('classify_task', dict.fromkeys(('scope', 'reasoning', 'ambiguity', 'dependencies', 'risk', 'context'), 1))
        self.assertEqual(result['mode'], 'advisory-only')
        self.assertFalse(result['actual_model_switched'])
        with self.assertRaises(ValueError):
            self.skills.call('classify_task', dict.fromkeys(('scope', 'reasoning', 'ambiguity', 'dependencies', 'risk', 'context'), 10))

    def test_render_actual_artifacts_and_confine_symlinks(self):
        (self.root / 'app.py').write_text('import pandas as pd\ndef transform_data():\n    frame = pd.read_csv("input.csv")\n    return frame.transform(lambda x: x)\n')
        (self.root / 'requirements.txt').write_text('pandas\n')
        result = self.skills.call('render_architecture', {'paths': ['app.py', 'requirements.txt']})
        self.assertTrue(result['summary']['semantic_artifacts_preserved'])
        self.assertTrue(result['files'])
        self.assertTrue(any(f['path'].endswith('.svg') for f in result['files']))
        for f in result['files']:
            self.assertTrue((self.root / f['path']).is_file())
        (self.root / 'escape.py').symlink_to('/etc/passwd')
        with self.assertRaises((OSError, ValueError)):
            self.skills.call('render_architecture', {'paths': ['escape.py']})

    def test_mcp_wire_and_unknown_tool(self):
        requests = [{'jsonrpc': '2.0', 'id': i, 'method': method, 'params': params} for i, (method, params) in enumerate([
            ('initialize', {}), ('tools/list', {}), ('tools/call', {'name': 'read_skill', 'arguments': {'skill': 'ui-ux-design-pro'}}),
            ('tools/call', {'name': 'shell', 'arguments': {}})])]
        proc = subprocess.run([sys.executable, str(ROOT / 'runtime/skills_mcp.py'), '--root', str(self.root)], input='\n'.join(json.dumps(r) for r in requests) + '\n', capture_output=True, text=True, timeout=20, check=True)
        responses = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(len(responses), 4)
        self.assertEqual(len(responses[1]['result']['tools']), 4)
        self.assertIn('UI UX Design', responses[2]['result']['content'][0]['text'])
        self.assertTrue(responses[3]['result']['isError'])


if __name__ == '__main__':
    unittest.main()

import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from patch_web import patch, ANCHOR, MARKER


class AutoSkillsTests(unittest.TestCase):
    def test_patch_is_idempotent_and_preserves_original_code(self):
        original = 'before\n' + ANCHOR + '\nafter'
        updated = patch(original)
        self.assertEqual(patch(updated), updated)
        self.assertIn(ANCHOR, updated)
        self.assertEqual(updated.split('\n' + MARKER)[0].replace('\n  strataApplyAutoSkills(body, mcpInfo);', ''), original)

    def test_patch_refuses_missing_or_ambiguous_anchor(self):
        for source in ('unrelated app', ANCHOR + '\n' + ANCHOR):
            with self.assertRaises(ValueError):
                patch(source)

    @unittest.skipUnless(shutil.which('node'), 'Node required for actual web request behavior')
    def test_web_request_gating_and_override_preservation(self):
        # Execute the actual shipped helper, rather than reimplementing its logic.
        script = 'const STRATA_AUTO_SKILLS_PROMPT = ' + json.dumps((ROOT / 'runtime/auto_skills_prompt.txt').read_text()) + ';\n'
        script += (ROOT / 'runtime/auto_skills.js').read_text()
        script += '''
const assert = require('node:assert/strict');
const ready = {servers: [{name: 'skills', status: 'ready', tools: [{name: 'skills__read_skill'}]}]};
const cases = [
  [{}, ready], [{strata_mcp: false}, ready], [{strata_mcp: 'true'}, ready],
  [{strata_mcp: true}, {servers: []}],
  [{strata_mcp: true}, {servers: [{...ready.servers[0], status: 'failed'}]}],
  [{strata_mcp: true}, {servers: [{...ready.servers[0], tools: []}]}]
];
for (const [flags, info] of cases) {
  const body = {...flags, messages: [{role: 'user', content: 'hello'}]};
  const before = JSON.stringify(body);
  strataApplyAutoSkills(body, info);
  assert.equal(JSON.stringify(body), before);
}
for (const text of ['fix app.py', 'use architecture-visualizer', 'do not use any skills', '2+2?']) {
  const original = [{role: 'system', content: 'reply in Chinese'}, {role: 'user', content: text}];
  const body = {strata_mcp: true, messages: original};
  strataApplyAutoSkills(body, ready);
  assert.equal(body.messages[0].role, 'system');
  assert.equal(body.messages[0].content, STRATA_AUTO_SKILLS_PROMPT);
  assert.deepEqual(body.messages.slice(1), original);
  assert.equal(original.length, 2);
}
assert.match(STRATA_AUTO_SKILLS_PROMPT, /Explicit user choices take precedence/);
assert.match(STRATA_AUTO_SKILLS_PROMPT, /simple factual questions/);
'''
        subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True, timeout=20)


if __name__ == '__main__':
    unittest.main()

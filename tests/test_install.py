import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

INSTALL = Path(__file__).resolve().parents[1] / 'install.py'


class InstallTests(unittest.TestCase):
    def test_idempotent_install_backup_and_remove(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'config.json'
            original = {'model': 'local', 'mcp_servers': {'workspace': {'command': 'existing'}}}
            config.write_text(json.dumps(original))
            command = [sys.executable, str(INSTALL), '--config', str(config)]
            for _ in range(2):
                subprocess.run(command, check=True, capture_output=True)
            changed = json.loads(config.read_text())
            self.assertEqual(changed['mcp_servers']['workspace'], original['mcp_servers']['workspace'])
            self.assertIn('skills', changed['mcp_servers'])
            self.assertEqual(json.loads(config.with_name('config.json.before-custom-skills').read_text()), original)
            subprocess.run([*command, '--remove'], check=True, capture_output=True)
            self.assertEqual(json.loads(config.read_text()), original)

    def test_refuse_unrelated_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'config.json'
            original = '{"mcp_servers":{"skills":{"command":"other"}}}'
            config.write_text(original)
            result = subprocess.run([sys.executable, str(INSTALL), '--config', str(config)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(config.read_text(), original)


if __name__ == '__main__':
    unittest.main()

"""Run focused and original asset tests from a writable disposable Docker copy."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
commands = [
    ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], root),
    ([sys.executable, 'skills/codex-model-router/scripts/route_task.py', '--self-test'], root),
    ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], root / 'skills/project-architecture-workflow'),
    ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], root / 'skills/surgical-coding-debug'),
    ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], root / 'skills/architecture-visualizer/package'),
]
for command, cwd in commands:
    print(f'CHECK: {cwd.relative_to(root)}: {command}', flush=True)
    subprocess.run(command, cwd=cwd, check=True, timeout=120, env={**os.environ, 'PYTHONPATH': str(cwd)})

"""Install package-specific web policy without changing Strata's API server."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKER = '// strata-custom-skills automatic selection v1'
ANCHOR = '  if (settings.mcp !== false && mcpInfo.tools > 0) body.strata_mcp = true;   // this server may run MCP tools for it'


def patch(source):
    if MARKER in source:
        return source
    if source.count(ANCHOR) != 1:
        raise ValueError('Unsupported Strata web app: expected one MCP request anchor; no changes made')
    policy = (ROOT / 'auto_skills_prompt.txt').read_text(encoding='utf-8').strip()
    helper = (ROOT / 'auto_skills.js').read_text(encoding='utf-8')
    return (source.replace(ANCHOR, ANCHOR + '\n  strataApplyAutoSkills(body, mcpInfo);')
            + '\n' + MARKER + '\nconst STRATA_AUTO_SKILLS_PROMPT = '
            + json.dumps(policy, ensure_ascii=False) + ';\n' + helper)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('app', type=Path)
    args = parser.parse_args()
    original = args.app.read_text(encoding='utf-8')
    updated = patch(original)
    if updated != original:
        args.app.write_text(updated, encoding='utf-8')

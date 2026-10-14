"""Explicitly add/remove this package's MCP entry in a Strata JSON config."""
import argparse
import json
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--package-root', default='/opt/strata/custom-skills')
    parser.add_argument('--python', default='/opt/strata/.venv/bin/python')
    parser.add_argument('--workspace', default='/workspace')
    parser.add_argument('--remove', action='store_true')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    entry = {'command': args.python, 'args': [args.package_root.rstrip('/') + '/runtime/skills_mcp.py', '--root', args.workspace], 'cwd': args.workspace}
    servers = config.setdefault('mcp_servers', {})
    previous = servers.get('skills')
    if args.remove:
        if previous != entry:
            raise SystemExit('Refusing removal: skills entry is absent or owned by another configuration')
        del servers['skills']
    else:
        if previous is not None and previous != entry:
            raise SystemExit('Refusing to overwrite an existing unrelated skills server')
        servers['skills'] = entry
    backup = args.config.with_name(args.config.name + '.before-custom-skills')
    if not backup.exists():
        shutil.copyfile(args.config, backup)
    temporary = args.config.with_name(args.config.name + '.skills-tmp')
    temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(args.config)
    print('Removed skills MCP entry' if args.remove else 'Installed skills MCP entry; recreate/restart Strata to load it')


if __name__ == '__main__':
    main()

"""Exercise real Strata MCP skill loading; saves evidence only when explicitly run."""
import argparse
import json
from pathlib import Path
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--url', default='http://127.0.0.1:8080')
parser.add_argument('--automatic', action='store_true', help='Test the web policy with an implicit debugging task')
args = parser.parse_args()
body = {'model': 'strata', 'strata_mcp': True, 'stream': False, 'max_tokens': 512,
        'reasoning_effort': 'none', 'temperature': 0.1,
        'messages': [{'role': 'system', 'content': 'Use the provided tools when requested. Never claim a tool succeeded without its result. Reply briefly in Traditional Chinese.'},
                     {'role': 'user', 'content': '請實際呼叫 skills 的 read_skill 工具，skill 設為 surgical-coding-debug，path 設為 SKILL.md。讀取後，用繁體中文一句話說明這個 skill 的用途。只需這個工具，不用修改任何檔案。'}]}
if args.automatic:
    body['messages'] = [
        {'role': 'system', 'content': (Path(__file__).resolve().parents[1] / 'runtime/auto_skills_prompt.txt').read_text(encoding='utf-8').strip()},
        {'role': 'user', 'content': '請幫我除錯 workspace 裡的 auto-skill-check.py。空清單時 average 會除以零；先讀檔並分析，這次只說明應如何修正，不要修改檔案。'}]
    body['max_tokens'] = 1536
req = urllib.request.Request(args.url + '/v1/chat/completions', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=1800) as response:
    result = json.load(response)
message = result['choices'][0]['message']
events = message.get('strata_mcp', [])
call_ids = {event.get('id') for event in events if event.get('event') == 'call'
            and event.get('name') == 'skills__read_skill'
            and 'surgical-coding-debug' in json.dumps(event.get('arguments', {}))}
passed = any(event.get('event') == 'result' and event.get('id') in call_ids
             and event.get('ok') is True and 'Surgical Coding' in event.get('text', '')
             for event in events)
evidence = {'passed': passed, 'request': body, 'response': result}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'passed': passed, 'events': [{k: e.get(k) for k in ('event', 'name', 'id', 'arguments', 'ok', 'chars', 'truncated') if k in e} for e in events], 'reply': message.get('content')}, ensure_ascii=False, indent=2))
if not passed:
    raise SystemExit('No confirmed read_skill tool event in model response')

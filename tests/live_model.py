"""Exercise real Strata MCP skill loading; saves evidence only when explicitly run."""
import argparse
import json
from pathlib import Path
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--url', default='http://127.0.0.1:8080')
args = parser.parse_args()
body = {'model': 'strata', 'strata_mcp': True, 'stream': False, 'max_tokens': 512,
        'reasoning_effort': 'none', 'temperature': 0.1,
        'messages': [{'role': 'system', 'content': 'Use the provided tools when requested. Never claim a tool succeeded without its result. Reply briefly in Traditional Chinese.'},
                     {'role': 'user', 'content': '請實際呼叫 skills 的 read_skill 工具，skill 設為 surgical-coding-debug，path 設為 SKILL.md。讀取後，用繁體中文一句話說明這個 skill 的用途。只需這個工具，不用修改任何檔案。'}]}
req = urllib.request.Request(args.url + '/v1/chat/completions', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=600) as response:
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
print(json.dumps({'passed': passed, 'events': events, 'reply': message.get('content')}, ensure_ascii=False, indent=2))
if not passed:
    raise SystemExit('No confirmed read_skill tool event in model response')

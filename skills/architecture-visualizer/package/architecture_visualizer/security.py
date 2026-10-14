"""Secret detection and recursive artifact redaction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

REDACTED = "<redacted>"
_KEY_VALUE = re.compile(
    r"(?i)(?P<key>(?:api[_-]?key|secret|token|password|passwd|pwd|private[_-]?key|client[_-]?secret|connection[_-]?string))"
    r"(?P<sep>\s*[:=]\s*)(?P<quote>['\"]?)(?P<value>[^\s,'\"}]+)(?P=quote)"
)
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{8,}=*")
_URL_CREDENTIAL = re.compile(r"(?P<scheme>[a-z][a-z0-9+.-]*://)(?P<creds>[^/@\s:]+:[^/@\s]+)@", re.I)
_TOKENISH = re.compile(r"\b(?:sk|ghp|glpat|xox[baprs])[-_][A-Za-z0-9_-]{12,}\b", re.I)
_PROVIDER_TOKEN = re.compile(r"\b(?:AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{20,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,})\b")
_PRIVATE_KEY = re.compile(r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----[\s\S]*?-----END(?: [A-Z]+)? PRIVATE KEY-----", re.I)
_QUOTED_KEY_VALUE = re.compile(r"(?i)(?P<prefix>['\"](?:api[_-]?key|secret|token|password|passwd|pwd|private[_-]?key|client[_-]?secret|connection[_-]?string)['\"]\s*:\s*)(?P<quote>['\"]?)(?P<value>[^\s,'\"}]+)(?P=quote)")


def env_key_names(path: Path) -> list[str]:
    """Return key names only; values never leave this function."""
    keys: list[str] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key = stripped.split("=", 1)[0].strip()
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                keys.append(key)
    except OSError:
        return []
    return sorted(set(keys))


def redact_text(value: str, known_secrets: Iterable[str] = ()) -> str:
    text = value
    for secret in sorted({s for s in known_secrets if len(s) >= 4}, key=len, reverse=True):
        text = text.replace(secret, REDACTED)
    text = _PRIVATE_KEY.sub(REDACTED, text)
    text = _QUOTED_KEY_VALUE.sub(lambda m: f"{m.group('prefix')}{REDACTED}", text)
    text = _KEY_VALUE.sub(lambda m: f"{m.group('key')}{m.group('sep')}{REDACTED}", text)
    text = _BEARER.sub(f"Bearer {REDACTED}", text)
    text = _URL_CREDENTIAL.sub(lambda m: f"{m.group('scheme')}{REDACTED}@", text)
    text = _TOKENISH.sub(REDACTED, text)
    text = _PROVIDER_TOKEN.sub(REDACTED, text)
    return text


def redact(value: Any, known_secrets: Iterable[str] = ()) -> Any:
    if isinstance(value, str):
        return redact_text(value, known_secrets)
    if isinstance(value, list):
        return [redact(item, known_secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item, known_secrets) for item in value)
    if isinstance(value, dict):
        return {str(key): redact(item, known_secrets) for key, item in value.items()}
    return value


def contains_secret(value: Any) -> bool:
    text = str(value).replace(REDACTED, "")
    return bool(_BEARER.search(text) or _TOKENISH.search(text) or _PROVIDER_TOKEN.search(text) or _PRIVATE_KEY.search(text) or _QUOTED_KEY_VALUE.search(text) or _URL_CREDENTIAL.search(text) or _KEY_VALUE.search(text))

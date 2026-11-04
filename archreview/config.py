"""Minimal local .env reader for the two supported Meta settings.
No variable expansion, executable shell syntax, or arbitrary environment settings.
Existing terminal/Compose environment values take precedence.
"""
import os
from pathlib import Path

ALLOWED = {'MODEL_API_KEY','META_MODEL'}

def load_local_env(path: Path):
    if not path.is_file():return
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        stripped=line.strip()
        if not stripped or stripped.startswith('#') or '=' not in stripped:continue
        key,value=stripped.split('=',1)
        key=key.strip();value=value.strip()
        if key not in ALLOWED:continue
        if len(value)>=2 and value[0]==value[-1] and value[0] in ('"',"'"):
            value=value[1:-1]
        if not os.environ.get(key):os.environ[key]=value

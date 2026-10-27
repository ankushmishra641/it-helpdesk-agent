"""Read-only, reproducible fictional organization snapshot."""
import json
from functools import lru_cache
from src.config import ROOT_DIR
@lru_cache(maxsize=1)
def catalog():
    return json.loads((ROOT_DIR / 'data' / 'demo.json').read_text(encoding='utf-8'))

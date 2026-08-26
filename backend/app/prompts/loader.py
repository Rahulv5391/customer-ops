from pathlib import Path

import yaml

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    path = _PROMPTS_DIR / f"{name}.yaml"
    if not path.exists():
        return ""
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("instruction", "")

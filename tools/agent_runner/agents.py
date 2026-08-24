from pathlib import Path
from typing import List, Dict

AGENTS_DIR = Path("ai-specs/.agents")

def discover_agents() -> List[Dict]:
    agents = []
    if not AGENTS_DIR.exists():
        return agents
    for p in sorted(AGENTS_DIR.glob("*.md")):
        content = p.read_text(encoding="utf-8")
        name = p.stem
        # take first paragraph as short description
        lines = [ln for ln in content.splitlines() if ln.strip()]
        desc = lines[0] if lines else ""
        agents.append({"name": name, "path": str(p), "summary": desc})
    return agents

if __name__ == "__main__":
    for a in discover_agents():
        print(f"- {a['name']}: {a['path']}")

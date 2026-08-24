from pathlib import Path
from datetime import datetime


def write_draft(agent_name: str, content: str, out_dir: Path, dry_run: bool = False, allow_overwrite: bool = False) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    filename = f"draft-{agent_name}-{ts}.md"
    target = out_dir / filename
    # safety: avoid writing into src/ unless caller allowed it
    try:
        rp = target.resolve()
        if 'src' in rp.parts and not allow_overwrite:
            raise RuntimeError("Refusing to write draft inside 'src/'. Use allow_overwrite to override.")
    except RuntimeError:
        raise
    except Exception:
        pass
    if dry_run:
        print(f"[dry-run] would write draft to: {target}")
        return target
    target.write_text(content, encoding="utf-8")
    print(f"Wrote draft: {target}")
    return target

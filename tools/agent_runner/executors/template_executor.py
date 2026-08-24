from pathlib import Path

def render_template(agent_name: str, agent_text: str) -> str:
    # Simple template: header + first section of agent text
    title = f"# Draft from agent: {agent_name}\n\n"
    body = agent_text.strip()
    return title + body + "\n"

def write_rendered(agent_name: str, agent_text: str, out_dir: Path, dry_run: bool = False, allow_overwrite: bool = False) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    content = render_template(agent_name, agent_text)
    filename = f"template-{agent_name}.md"
    target = out_dir / filename
    try:
        rp = target.resolve()
        if 'src' in rp.parts and not allow_overwrite:
            raise RuntimeError("Refusing to write template inside 'src/'. Use allow_overwrite to override.")
    except RuntimeError:
        raise
    except Exception:
        pass
    if dry_run:
        print(f"[dry-run] would write rendered template to: {target}")
        return target
    target.write_text(content, encoding="utf-8")
    print(f"Wrote rendered template: {target}")
    return target

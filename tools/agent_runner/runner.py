#!/usr/bin/env python3
"""Simple agent-runner CLI (human-assisted by default)."""
import argparse
import subprocess
import sys
from pathlib import Path
from tools.agent_runner.agents import discover_agents
from tools.agent_runner.executors import human_executor, template_executor


OUT_BASE = Path("ai-specs/changes")


def list_agents():
    agents = discover_agents()
    if not agents:
        print("No agents found in ai-specs/.agents/")
        return
    for a in agents:
        print(f"- {a['name']}: {a['summary']}")


def safe_path_check(path: Path, allow_src: bool) -> bool:
    try:
        rp = path.resolve()
    except Exception:
        return False
    # Prevent accidental writes into src/ unless explicitly allowed
    if "src" in rp.parts and not allow_src:
        print("Refusing to write inside 'src/'. Use --allow-src to override.")
        return False
    return True


def git_commit(paths, message: str, author: str = None) -> int:
    cmds = [["git", "add"] + paths, ["git", "commit", "-m", message]]
    if author:
        cmds[1].extend(["--author", author])
    for cmd in cmds:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Git command failed: {' '.join(cmd)}")
            print(res.stdout)
            print(res.stderr)
            return res.returncode
    print("Committed changes locally.")
    return 0


def run_agent(agent_name: str, mode: str, dry_run: bool, out_base: Path, allow_src: bool, do_commit: bool, confirm: bool, commit_message: str, author: str):
    agents = {a['name']: a for a in discover_agents()}
    if agent_name not in agents:
        print(f"Agent not found: {agent_name}")
        return
    agent = agents[agent_name]
    agent_text = Path(agent['path']).read_text(encoding='utf-8')
    out_dir = out_base / agent_name
    if not safe_path_check(out_dir, allow_src):
        return
    target = None
    if mode == 'human':
        target = human_executor.write_draft(agent_name, agent_text, out_dir, dry_run=dry_run)
    elif mode == 'template':
        target = template_executor.write_rendered(agent_name, agent_text, out_dir, dry_run=dry_run)
    else:
        print(f"Unknown mode: {mode}")
        return

    # Optional commit flow
    if do_commit:
        if dry_run:
            print("Dry-run: skipping commit")
            return
        if not confirm:
            print("Refusing to commit without --confirm flag")
            return
        if target is None:
            print("No target to commit")
            return
        # perform git add + commit
        rel = str(target)
        code = git_commit([rel], commit_message or f"chore: add agent output {agent_name}", author)
        if code != 0:
            print("Git commit failed")
            return


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--list', action='store_true', help='List available agents')
    p.add_argument('--agent', help='Agent name to run')
    p.add_argument('--mode', choices=['human','template'], default='human')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--out', default=str(OUT_BASE), help='Output base directory')
    p.add_argument('--allow-src', action='store_true', help='Allow writing inside src/ directories')
    p.add_argument('--commit', action='store_true', help='If set, attempt to git commit generated files (requires --confirm)')
    p.add_argument('--confirm', action='store_true', help='Confirm potentially destructive actions like committing')
    p.add_argument('--message', help='Commit message to use when --commit is set')
    p.add_argument('--author', help='Author string for git commit (e.g. "Name <email>")')
    args = p.parse_args()
    if args.list:
        list_agents()
        return
    if not args.agent:
        print('Please provide --agent or use --list')
        return
    out_base = Path(args.out)
    run_agent(args.agent, args.mode, args.dry_run, out_base, args.allow_src, args.commit, args.confirm, args.message, args.author)


if __name__ == '__main__':
    main()

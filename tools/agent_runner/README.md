Agent Runner (scaffold)
=========================

Purpose
-------
Small CLI to discover `ai-specs/.agents/*.md` and generate draft artifacts in `ai-specs/changes/`.

Usage
-----
List agents:

```
python -m tools.agent_runner.runner --list
```

Generate a human-assisted draft (no commits):

```
python -m tools.agent_runner.runner --agent backend-developer --mode human
```

Generate a rendered template draft:

```
python -m tools.agent_runner.runner --agent backend-developer --mode template
```

Safety
------
- Default mode is `human` (writes drafts only). No automatic commits or network calls are performed.
- LLM executor is disabled by default; enabling requires explicit config and consent.

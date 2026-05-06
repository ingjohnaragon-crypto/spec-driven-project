"""
parse_agent.py — reads the agent block from openspec/config.yaml
Usage: py parse_agent.py <config_path> <agent_name>
Output: KEY=VALUE lines for shell eval
"""
import sys
import re

if len(sys.argv) < 3:
    sys.exit(1)

config_path = sys.argv[1]
target_agent = sys.argv[2]

with open(config_path, encoding="utf-8") as f:
    lines = f.readlines()

# Find "agents:" section
in_agents = False
agent_start = None

for i, line in enumerate(lines):
    stripped = line.rstrip()
    if re.match(r'^agents:\s*$', stripped):
        in_agents = True
        continue
    if in_agents:
        # Top-level key ends the section
        if stripped and not stripped.startswith(' '):
            break
        # Agent entry: 2-space indent
        m = re.match(r'^  ([a-zA-Z0-9_-]+):\s*$', stripped)
        if m and m.group(1) == target_agent:
            agent_start = i
            break

if agent_start is None:
    # Fallback defaults for unknown agents
    print(f"label={target_agent}")
    print("delivery=clipboard")
    print("command=null")
    print("args=")
    sys.exit(0)

# Read fields (4-space indented lines)
fields = {}
for line in lines[agent_start + 1:]:
    s = line.rstrip()
    if s and not s.startswith('    '):
        break
    m = re.match(r'^    ([a-zA-Z0-9_]+):\s*(.+)$', s)
    if m:
        key = m.group(1).strip()
        val = m.group(2).strip().strip('"').strip("'")
        if val.lower() == 'null':
            val = 'null'
        fields[key] = val

print(f"label={fields.get('label', target_agent)}")
print(f"delivery={fields.get('delivery', 'clipboard')}")
print(f"command={fields.get('command', 'null')}")
print(f"args={fields.get('args', '')}")

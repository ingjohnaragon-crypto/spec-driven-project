"""
parse_language.py — reads the language block from openspec/config.yaml
Usage: py parse_language.py <config_path> <language_code>
Output: KEY=VALUE lines for shell eval
"""
import sys
import re

if len(sys.argv) < 3:
    sys.exit(1)

config_path = sys.argv[1]
target_language = sys.argv[2]

with open(config_path, encoding="utf-8") as f:
    lines = f.readlines()

# Find "languages:" section
in_languages = False
language_start = None

for i, line in enumerate(lines):
    stripped = line.rstrip()
    if re.match(r'^languages:\s*$', stripped):
        in_languages = True
        continue
    if in_languages:
        # Top-level key ends the section
        if stripped and not stripped.startswith(' '):
            break
        # Language entry: 2-space indent
        m = re.match(r'^  ([a-zA-Z0-9_-]+):\s*$', stripped)
        if m and m.group(1) == target_language:
            language_start = i
            break

if language_start is None:
    # Fallback default for unknown languages
    print(f"label={target_language}")
    sys.exit(0)

# Read fields (4-space indented lines)
fields = {}
for line in lines[language_start + 1:]:
    s = line.rstrip()
    if s and not s.startswith('    '):
        break
    m = re.match(r'^    ([a-zA-Z0-9_]+):\s*(.+)$', s)
    if m:
        key = m.group(1).strip()
        val = m.group(2).strip().strip('"').strip("'")
        fields[key] = val

print(f"label={fields.get('label', target_language)}")

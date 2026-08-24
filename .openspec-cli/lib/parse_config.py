#!/usr/bin/env python3
"""Read the active stack and agent settings from OpenSpec config.yaml."""

import re
import sys


def parse_config(path):
    with open(path, encoding="utf-8") as config_file:
        lines = config_file.readlines()

    stack = None
    agent = None
    language = None
    values = {}
    section = None
    subsection = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = re.match(r"^stack:\s*([a-zA-Z0-9_-]+)", line)
        if match:
            stack = match.group(1)
            continue
        match = re.match(r"^agent:\s*([a-zA-Z0-9_-]+)", line)
        if match:
            agent = match.group(1)
            continue
        match = re.match(r"^language:\s*([a-zA-Z0-9_-]+)", line)
        if match:
            language = match.group(1)
            continue

        section_match = re.match(r"^([a-zA-Z0-9_-]+):\s*$", line)
        if section_match:
            section = section_match.group(1)
            subsection = None
            continue

        subsection_match = re.match(r"^  ([a-zA-Z0-9_-]+):\s*$", line)
        if subsection_match and section in ("stacks", "agents"):
            subsection = subsection_match.group(1)
            continue

        value_match = re.match(r"^    ([a-zA-Z0-9_-]+):\s*(.*)$", line)
        if value_match and section and subsection:
            key, value = value_match.groups()
            values[(section, subsection, key)] = value.strip().strip('"').strip("'")

    if not stack:
        raise ValueError("active stack is missing")

    output = {
        "label": values.get(("stacks", stack, "label"), stack),
        "build_command": values.get(("stacks", stack, "build_command"), ""),
        "test_command": values.get(("stacks", stack, "test_command"), ""),
        "run_command": values.get(("stacks", stack, "run_command"), ""),
        "lint_command": values.get(("stacks", stack, "lint_command"), ""),
        "coverage_command": values.get(("stacks", stack, "coverage_command"), ""),
        "agent": values.get(("stacks", stack, "agent"), ""),
        "standards": values.get(("stacks", stack, "standards"), ""),
        "language": language or "en",
    }
    for key, value in output.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: parse_config.py CONFIG_PATH")
    parse_config(sys.argv[1])

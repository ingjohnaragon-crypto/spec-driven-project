import sys, re

with open(sys.argv[1], encoding="utf-8") as f:
    for line in f:
        m = re.match(r"^stack:\s*([a-zA-Z0-9_-]+)", line)
        if m:
            print(m.group(1).strip())
            break

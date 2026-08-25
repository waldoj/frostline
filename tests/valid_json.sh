#!/bin/bash

# Verify that every JSON file in api/ parses. Done in a single Python process,
# since there are tens of thousands of files.
python3 - <<'PYTHON'
import glob
import json
import sys

failed = []
for path in glob.iglob('api/*.json'):
    try:
        with open(path) as file:
            json.load(file)
    except (ValueError, OSError) as error:
        failed.append(f"{path}: {error}")

for failure in failed:
    print(f"Invalid JSON: {failure}")

print(f"checked {len(glob.glob('api/*.json'))} files, {len(failed)} invalid")
sys.exit(1 if failed else 0)
PYTHON

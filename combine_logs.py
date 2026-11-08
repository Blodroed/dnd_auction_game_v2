#!/usr/bin/env python3
"""
jsonl_combine_agent_range.py — Concatenate JSONL files for a specific agent and round range.

Usage (PowerShell):
  python jsonl_combine_agent_range.py ^
    --dir agent_666/logs ^
    --agent agent_3259117be28efac376fe1936c00abeadac03d1e6aa13398ff17f91b9eb99d8c6 ^
    --start 23 --end 30 ^
    --output combined_agent_n23_n30.jsonl

Notes:
- Finds files named: <agent>_n<round>.jsonl within --dir.
- Sorts by <round> ascending and concatenates in that order.
- Writes lines as-is (no validation), skips empty lines.
"""

import sys
import argparse
from pathlib import Path
import re

def find_files_by_agent_and_range(root: Path, agent: str, start: int, end: int):
    # Regex for agent_n<round>.jsonl
    pattern = re.compile(rf"^{re.escape(agent)}_n(\d+)\.jsonl$")
    matches = []
    for p in root.glob("*.jsonl"):
        m = pattern.match(p.name)
        if not m:
            continue
        try:
            n = int(m.group(1))
        except ValueError:
            continue
        if start <= n <= end:
            matches.append((n, p))
    # Sort by round number ascending
    matches.sort(key=lambda t: t[0])
    return [p for _, p in matches]

def combine_jsonl_files(inputs, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    count_in = 0
    count_out = 0

    with output.open("w", encoding="utf-8") as out_f:
        for inp in inputs:
            with inp.open("r", encoding="utf-8", errors="ignore") as in_f:
                for line in in_f:
                    count_in += 1
                    if not line.strip():
                        continue
                    out_f.write(line)
                    if not line.endswith("\n"):
                        out_f.write("\n")
                    count_out += 1

    print(f"Combined {len(inputs)} files.")
    for i, fp in enumerate(inputs, 1):
        print(f"  {i}. {fp}")
    print(f"Done. Read {count_in} lines; wrote {count_out} records to {output}")

def main():
    ap = argparse.ArgumentParser(description="Concatenate JSONL files for an agent in a round range.")
    ap.add_argument("--dir", required=True, help="Directory containing JSONL files to scan.")
    ap.add_argument("--agent", required=True, help="Agent id prefix (full exact string in filenames).")
    ap.add_argument("--start", type=int, required=True, help="Start round (inclusive).")
    ap.add_argument("--end", type=int, required=True, help="End round (inclusive).")
    ap.add_argument("--output", required=True, help="Output JSONL file path.")
    args = ap.parse_args()

    root = Path(args.dir)
    if not root.exists():
        print(f"Error: directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    files = find_files_by_agent_and_range(root, args.agent, args.start, args.end)
    if not files:
        print("No matching files found for given agent and range.", file=sys.stderr)
        sys.exit(2)

    out_path = Path(args.output)
    combine_jsonl_files(files, out_path)

if __name__ == "__main__":
    main()
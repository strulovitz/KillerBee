#!/usr/bin/env python3
"""
Integration step at each tier of the hive.

Takes child reports (text from lower tiers) + this tier's own gestalt
observation, builds a prompt, calls run_reasoner.py, returns an integrated
paragraph for this tier.

Chapter 12 principle: the parent has TWO sources of information:
1. Her own eyes (low-res gestalt) — she sees WHERE things are
2. The workers' text reports — they see WHAT the details are
She integrates by placing the workers' details onto her spatial/temporal map.
"""
import argparse
import json
import os
import sys

# Import the reasoner directly
from run_reasoner import run_ollama


INTEGRATION_PROMPT = """You are a coordinator in a hierarchical AI system. You have two sources of information:

1. YOUR OWN OBSERVATION (low-resolution gestalt — you see the big picture but not fine details):
{gestalt_observation}

2. DETAILED REPORTS FROM YOUR WORKERS (each worker saw a small piece at high resolution):
{child_reports}

Your job: integrate the workers' detailed reports with your own big-picture view. Produce ONE coherent paragraph that combines:
- The spatial/temporal structure from your own observation (where things are, when things happen)
- The specific details from the workers' reports (names, numbers, exact words, fine features)

Do NOT list the workers' reports separately. Write a single integrated description as if you saw everything yourself. Be specific and factual — use the workers' details, not vague summaries."""


def main():
    parser = argparse.ArgumentParser(description="Integrate child reports with gestalt")
    parser.add_argument("--model", required=True, help="Ollama model tag for reasoning")
    parser.add_argument("--gestalt", required=True,
                        help="Text file with this tier's gestalt observation")
    parser.add_argument("--children-dir", required=True,
                        help="Directory of child report text files")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    # Read gestalt
    with open(args.gestalt) as f:
        gestalt_text = f.read().strip()

    # Read all child reports
    reports = []
    children_files = sorted(os.listdir(args.children_dir))
    for fname in children_files:
        fpath = os.path.join(args.children_dir, fname)
        if os.path.isfile(fpath):
            with open(fpath) as f:
                content = f.read().strip()
            reports.append(f"[{fname}]:\n{content}")

    if not reports:
        print("ERROR: no child reports found", file=sys.stderr)
        sys.exit(1)

    child_reports_text = "\n\n".join(reports)

    # Build prompt
    prompt = INTEGRATION_PROMPT.format(
        gestalt_observation=gestalt_text,
        child_reports=child_reports_text
    )

    # Run reasoner
    result = run_ollama(args.model, prompt, args.ollama_url)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Written to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()

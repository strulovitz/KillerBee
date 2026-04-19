"""Submit a KillerBee job via direct SQL INSERT.

Usage:
    ./killerbee-venv/bin/python /tmp/submit_q.py <task-file>

Inserts a SwarmJob row with swarm_id=1, beekeeper_id=2 (beekeeper_demo),
status='pending'. Raja's poll of /api/swarm/1/jobs/pending picks it up.
"""
import os
import sqlite3
import sys

DB_PATH = "/home/nir/KillerBee/instance/killerbee.db"


def main():
    if len(sys.argv) < 2:
        print("Usage: submit_q.py <task-file>", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], "r") as f:
        task = f.read().strip()
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO swarm_jobs (swarm_id, beekeeper_id, task, status, "
        "components_total, components_completed, created_at) "
        "VALUES (1, 2, ?, 'pending', 0, 0, datetime('now'))",
        (task,),
    )
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    print(f"Submitted job_id={job_id} length={len(task)} chars")


if __name__ == "__main__":
    main()

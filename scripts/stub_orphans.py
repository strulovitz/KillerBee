"""Stub orphaned job_components whose result-POST failed mid-night.

Bees complete work locally, POST result to KillerBee, but the Network-is-unreachable
retry-exhaustion pattern causes the POST to fail silently. The bee logs the
exception and moves on. Component stays `processing` forever in the DB.
get_my_work filters to status=pending so the bee never re-picks up its own orphan,
and the parent bee (polling /api/component/X/status) never sees completion.

This script stubs specified component IDs as completed with a disclosure string,
so the parent bee's calibration or combine step can unblock.

Usage:
    ./killerbee-venv/bin/python scripts/stub_orphans.py 421 425 471
"""
import os
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance", "killerbee.db")


def stub_orphan(cur, comp_id):
    row = cur.execute(
        "SELECT id, job_id, member_id, status, level FROM job_components WHERE id = ?",
        (comp_id,),
    ).fetchone()
    if row is None:
        print(f"  {comp_id}: NOT FOUND")
        return False
    if row["status"] == "completed":
        print(f"  {comp_id}: already completed, skipping")
        return False

    note = (
        f"[STUBBED-ORPHAN id={comp_id} job={row['job_id']} member={row['member_id']} "
        f"level={row['level']} prev_status={row['status']}] "
        f"Bee likely finished work but result POST lost to Network-is-unreachable "
        f"retry-exhaustion. Stubbed at MoE-night 2026-04-19 to unblock parent bee."
    )
    cur.execute(
        "UPDATE job_components SET status = 'completed', result = ? WHERE id = ?",
        (note, comp_id),
    )
    print(f"  {comp_id}: stubbed (was {row['status']} on member_id={row['member_id']})")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: stub_orphans.py <comp_id> [<comp_id> ...]", file=sys.stderr)
        sys.exit(1)

    ids = [int(a) for a in sys.argv[1:]]
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("BEGIN IMMEDIATE")
    n = sum(1 for i in ids if stub_orphan(cur, i))
    conn.commit()
    conn.close()
    print(f"Stubbed {n} of {len(ids)} components at {datetime.utcnow().isoformat()}Z")


if __name__ == "__main__":
    main()

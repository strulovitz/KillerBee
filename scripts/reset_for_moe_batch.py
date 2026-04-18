"""Reset KillerBee DB state for MoE batch start (2026-04-19 MoE Night 2).

Keeps users, swarms, swarm_members structure, and parent_member_id relationships
(the hard-won topology fix from Dense Night 1). Resets per-member calibration
numbers so MoE calibration starts fresh without Dense-qwen3 bias. Marks last
night's 45 zombie calibration components as completed with an ABANDONED result
string so their row history is preserved but they are invisible to
get_my_work (which filters by status pending/processing).

Run from the KillerBee repo root:
    ./killerbee-venv/bin/python scripts/reset_for_moe_batch.py
"""
import os
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance", "killerbee.db")

ABANDONED_NOTE = (
    "[ABANDONED: Dense-batch Job 1 calibration cascade deadlock never completed, "
    "marked at MoE pre-flight 2026-04-19]"
)


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("BEGIN IMMEDIATE")

    pre_zombies = cur.execute(
        "SELECT status, COUNT(*) AS n FROM job_components "
        "WHERE status IN ('pending', 'processing') GROUP BY status"
    ).fetchall()
    print("Pre-cleanup zombie components:", [dict(r) for r in pre_zombies])

    cur.execute(
        "UPDATE job_components SET status = 'completed', result = ? "
        "WHERE status IN ('pending', 'processing')",
        (ABANDONED_NOTE,),
    )
    print(f"Marked {cur.rowcount} zombie components as completed with ABANDONED note.")

    pre_buzz = cur.execute(
        "SELECT COUNT(*) FROM swarm_members WHERE fraction IS NOT NULL "
        "OR capacity IS NOT NULL OR buzzing_speed IS NOT NULL "
        "OR buzzing_quality IS NOT NULL OR buzzing IS NOT NULL"
    ).fetchone()[0]
    print(f"Pre-cleanup swarm_members with non-NULL buzzing fields: {pre_buzz}")

    cur.execute(
        "UPDATE swarm_members SET fraction = NULL, capacity = NULL, "
        "buzzing_speed = NULL, buzzing_quality = NULL, buzzing = NULL"
    )
    print(f"Zeroed buzzing fields on {cur.rowcount} swarm_members (parent_member_id preserved).")

    conn.commit()
    conn.close()

    print(f"Cleanup complete at {datetime.utcnow().isoformat()}Z")


if __name__ == "__main__":
    main()

"""Submit a question to the Phase 3 Hive as beekeeper_demo via direct DB insert.

Bypasses the CSRF-guarded HTML form. Returns the new job_id so the caller can
poll /api/job/<id> or read the DB for completion.
"""
import argparse
import sys

from app import app, db
from models import SwarmJob, User, Swarm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--swarm-id", type=int, default=1)
    parser.add_argument("--beekeeper", type=str, default="beekeeper_demo")
    parser.add_argument("--task-file", type=str, required=True,
                        help="Path to a text file with the question")
    parser.add_argument("--tag", type=str, default="",
                        help="Optional tag prepended as [TAG] to task")
    args = parser.parse_args()

    with open(args.task_file) as f:
        task_body = f.read().strip()

    if args.tag:
        task_body = f"[{args.tag}]\n\n{task_body}"

    with app.app_context():
        swarm = Swarm.query.get(args.swarm_id)
        if not swarm:
            print(f"Swarm {args.swarm_id} not found")
            sys.exit(1)
        bk = User.query.filter_by(username=args.beekeeper).first()
        if not bk:
            print(f"Beekeeper {args.beekeeper} not found")
            sys.exit(1)

        job = SwarmJob(
            swarm_id=swarm.id,
            beekeeper_id=bk.id,
            task=task_body,
        )
        db.session.add(job)
        db.session.commit()
        print(f"Submitted job_id={job.id} swarm={swarm.name} "
              f"beekeeper={bk.username} tag={args.tag or '<none>'} "
              f"task_length={len(task_body)}")


if __name__ == "__main__":
    main()

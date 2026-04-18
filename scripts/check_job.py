"""Check a SwarmJob's status + component breakdown. Exit 0 if completed, 1 otherwise."""
import sys

from app import app, db
from models import SwarmJob, JobComponent

job_id = int(sys.argv[1])
with app.app_context():
    j = db.session.get(SwarmJob, job_id)
    if not j:
        print(f'Job {job_id} not found')
        sys.exit(1)
    comps = JobComponent.query.filter_by(job_id=job_id).all()
    sc = {}
    for c in comps:
        sc[c.status] = sc.get(c.status, 0) + 1
    print(f'Job {job_id} status={j.status} comps={len(comps)} {sc}')
    sys.exit(0 if j.status == 'completed' else 1)

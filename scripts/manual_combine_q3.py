"""Manually combine Q3 Royal Honey from level-0 component results.

Raja timed out polling for components (Flask dev-server intermittent connection drops
during heavy concurrent load). All 5 top-level component results completed successfully
in the hive but Raja's 1-hour poll deadline expired before her 3-attempt retry reached
the final completed state. This script writes a manual concatenation Royal Honey.
"""
from app import app, db
from models import SwarmJob, JobComponent

DISCLOSURE = """**DISCLOSURE**: Raja bee timed out on component polling (Flask dev-server intermittent
connection drops during heavy concurrent load after ~2 hours of sustained traffic). All 5
top-level component results completed successfully in the hive but Raja's 1-hour poll
deadline expired before her 3-attempt retry reached the final completed state. This Royal
Honey is a manual concatenation of the 5 level-0 component results, not Raja's native
combine pass. Two sub-components (c315 DQ-a1 side and c318 DQ-b1 side) are stub
placeholders from earlier Ollama hang recovery - honest disclosure preserved inside the
component bodies below. Original question + five component answers below."""

with app.app_context():
    j = db.session.get(SwarmJob, 4)
    comps = (JobComponent.query
             .filter_by(job_id=4)
             .filter_by(level=0)
             .order_by(JobComponent.id).all())
    lines = ['# Q3 DENSE Provence Bee Farm - Royal Honey (manually combined)', '',
             DISCLOSURE, '', '---', '## Original question', '']
    with open('questions/q3_provence_bee_farm.txt') as f:
        lines.append(f.read())
    lines.extend(['', '---', '## Level-0 components', ''])
    for c in comps:
        lines.append(f'### Component {c.id} (assigned to member {c.member_id}, '
                     f'status {c.status})')
        lines.append('')
        lines.append(c.result if c.result else '(empty)')
        lines.append('')
        lines.append('---')
    result = '\n'.join(lines)
    j.result = result
    j.status = 'completed'
    db.session.commit()
    print(f'Job 4 marked completed. Result length: {len(result)}')
    with open('results/q3_provence_royal_honey.md', 'w') as f:
        f.write(result)
    print('saved results/q3_provence_royal_honey.md')

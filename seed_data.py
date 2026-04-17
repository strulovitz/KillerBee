"""
seed_data.py — Populate KillerBee with demo data (Phase 3 — 15 VMs)
===================================================================
Creates ONLY users and a swarm. Members are NOT pre-created —
bees register themselves when they start up.

Phase 3 hierarchy: RajaBee -> 2 GiantQueens -> 4 DwarfQueens -> 8 Workers (15 bees).
"""

from app import app, db
from models import User, Swarm

with app.app_context():
    db.create_all()

    if User.query.first():
        print("Database already has data. Skipping seed.")
        exit(0)

    users = []

    raja = User(username='raja_nir', email='raja@example.com', role='raja')
    raja.set_password('password')
    users.append(raja)

    beekeeper = User(username='beekeeper_demo', email='bk@example.com', role='beekeeper')
    beekeeper.set_password('password')
    users.append(beekeeper)

    for name in ['queen_giant_a', 'queen_giant_b']:
        u = User(username=name, email=f'{name}@example.com', role='giant_queen')
        u.set_password('password')
        users.append(u)

    for name in ['queen_dwarf_a1', 'queen_dwarf_a2', 'queen_dwarf_b1', 'queen_dwarf_b2']:
        u = User(username=name, email=f'{name}@example.com', role='dwarf_queen')
        u.set_password('password')
        users.append(u)

    for name in ['worker_a1', 'worker_a2', 'worker_a3', 'worker_a4',
                 'worker_b1', 'worker_b2', 'worker_b3', 'worker_b4']:
        u = User(username=name, email=f'{name}@example.com', role='worker')
        u.set_password('password')
        users.append(u)

    db.session.add_all(users)
    db.session.commit()

    swarm = Swarm(
        name='Phase 3 Hive',
        description='Phase 3 full 4-level hierarchy across 15 VMs: RajaBee -> 2 GiantQueens -> 4 DwarfQueens -> 8 Workers.',
        raja_id=raja.id,
        raja_model='qwen3:14b',
        specialty='research',
        max_queens=16,
        depth=4,
    )
    db.session.add(swarm)
    db.session.commit()

    print("Seed data created (Phase 3):")
    print(f"  Users ({len(users)}): {', '.join(u.username for u in users)}")
    print(f"  Password for all: 'password'")
    print(f"  Swarm: Phase 3 Hive (depth=4, no members yet — bees register themselves)")
    print(f"  Website: http://localhost:8877")

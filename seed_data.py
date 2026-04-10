"""
seed_data.py — Populate KillerBee with demo data
=================================================
Creates ONLY users and a swarm. Members are NOT pre-created —
bees register themselves when they start up.

This avoids showing fake "online" members that aren't actually running.
"""

from app import app, db
from models import User, Swarm

with app.app_context():
    db.create_all()

    # Check if already seeded
    if User.query.first():
        print("Database already has data. Skipping seed.")
        exit(0)

    # Create users (they register as members when their bee process starts)
    raja = User(username='raja_nir', email='raja@example.com', role='raja')
    raja.set_password('password')

    giant_queen = User(username='queen_giant', email='giantqueen@example.com', role='giant_queen')
    giant_queen.set_password('password')

    dwarf_queen1 = User(username='queen_alpha', email='queen1@example.com', role='dwarf_queen')
    dwarf_queen1.set_password('password')

    dwarf_queen2 = User(username='queen_bravo', email='queen2@example.com', role='dwarf_queen')
    dwarf_queen2.set_password('password')

    beekeeper = User(username='beekeeper_demo', email='bk@example.com', role='beekeeper')
    beekeeper.set_password('password')

    worker1 = User(username='worker_alpha', email='worker1@example.com', role='worker')
    worker1.set_password('password')

    worker2 = User(username='worker_bravo', email='worker2@example.com', role='worker')
    worker2.set_password('password')

    db.session.add_all([raja, giant_queen, dwarf_queen1, dwarf_queen2, beekeeper, worker1, worker2])
    db.session.commit()

    # Create a Swarm (but NO members — they register when bees start)
    swarm = Swarm(
        name='Alpha Swarm',
        description='General-purpose hierarchical hive for research and analysis tasks.',
        raja_id=raja.id,
        raja_model='llama3.2:3b',
        specialty='research',
        max_queens=10,
        depth=3,
    )
    db.session.add(swarm)
    db.session.commit()

    print("Seed data created:")
    print(f"  Users: raja_nir, queen_giant, queen_alpha, queen_bravo, beekeeper_demo, worker_alpha, worker_bravo")
    print(f"  Password for all: 'password'")
    print(f"  Swarm: Alpha Swarm (no members yet — bees register themselves)")
    print(f"  Website: http://localhost:8877")

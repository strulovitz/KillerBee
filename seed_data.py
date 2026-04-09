"""
seed_data.py — Populate KillerBee with demo data
=================================================
Run this once to create demo users, a Swarm, and members.
"""

from app import app, db
from models import User, Swarm, SwarmMember

with app.app_context():
    db.create_all()

    # Check if already seeded
    if User.query.first():
        print("Database already has data. Skipping seed.")
        exit(0)

    # Create users
    raja = User(username='raja_nir', email='raja@example.com', role='raja')
    raja.set_password('password')

    queen1 = User(username='queen_alpha', email='queen1@example.com', role='queen')
    queen1.set_password('password')

    queen2 = User(username='queen_bravo', email='queen2@example.com', role='queen')
    queen2.set_password('password')

    beekeeper = User(username='beekeeper_demo', email='bk@example.com', role='beekeeper')
    beekeeper.set_password('password')

    worker = User(username='worker_demo', email='worker@example.com', role='worker')
    worker.set_password('password')

    db.session.add_all([raja, queen1, queen2, beekeeper, worker])
    db.session.commit()

    # Create a Swarm
    swarm = Swarm(
        name='Alpha Swarm',
        description='General-purpose hierarchical hive for research and analysis tasks.',
        raja_id=raja.id,
        raja_model='llama3.2:3b',
        specialty='research',
        max_queens=10,
    )
    db.session.add(swarm)
    db.session.commit()

    # Add Queens to the Swarm
    member1 = SwarmMember(
        swarm_id=swarm.id,
        user_id=queen1.id,
        endpoint='http://localhost:5000',
        member_type='queen',
        model_name='qwen2.5:1.5b',
        worker_count=2,
    )
    member2 = SwarmMember(
        swarm_id=swarm.id,
        user_id=queen2.id,
        endpoint='http://localhost:5001',
        member_type='queen',
        model_name='qwen2.5:1.5b',
        worker_count=3,
    )
    db.session.add_all([member1, member2])
    db.session.commit()

    print("Seed data created:")
    print(f"  Users: raja_nir, queen_alpha, queen_bravo, beekeeper_demo, worker_demo")
    print(f"  Password for all: 'password'")
    print(f"  Swarm: Alpha Swarm (2 Queens, 5 Workers)")
    print(f"  Website: http://localhost:8877")

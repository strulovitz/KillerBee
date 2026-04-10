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

    # GiantQueen — mid-level coordinator (coordinates DwarfQueens, no Workers directly)
    giant_queen = User(username='queen_giant', email='giantqueen@example.com', role='giant_queen')
    giant_queen.set_password('password')

    # DwarfQueens — lowest-level coordinators with Workers directly under them
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

    # Create a Swarm
    swarm = Swarm(
        name='Alpha Swarm',
        description='General-purpose hierarchical hive for research and analysis tasks.',
        raja_id=raja.id,
        raja_model='llama3.2:3b',
        specialty='research',
        max_queens=10,
        depth=3,  # Raja -> GiantQueen -> DwarfQueen -> Worker
    )
    db.session.add(swarm)
    db.session.commit()

    # Add GiantQueen to the Swarm
    gq_member = SwarmMember(
        swarm_id=swarm.id,
        user_id=giant_queen.id,
        endpoint='http://localhost:5000',
        member_type='giant_queen',
        model_name='qwen2.5:3b',
        worker_count=5,
    )

    # Add DwarfQueens to the Swarm
    dq_member1 = SwarmMember(
        swarm_id=swarm.id,
        user_id=dwarf_queen1.id,
        endpoint='http://localhost:5001',
        member_type='dwarf_queen',
        model_name='qwen2.5:1.5b',
        worker_count=2,
    )
    dq_member2 = SwarmMember(
        swarm_id=swarm.id,
        user_id=dwarf_queen2.id,
        endpoint='http://localhost:5002',
        member_type='dwarf_queen',
        model_name='qwen2.5:1.5b',
        worker_count=3,
    )

    # Add Workers to the Swarm
    w_member1 = SwarmMember(
        swarm_id=swarm.id,
        user_id=worker1.id,
        endpoint='http://localhost:5003',
        member_type='worker',
        model_name='qwen2.5:0.5b',
        worker_count=1,
    )
    w_member2 = SwarmMember(
        swarm_id=swarm.id,
        user_id=worker2.id,
        endpoint='http://localhost:5004',
        member_type='worker',
        model_name='qwen2.5:0.5b',
        worker_count=1,
    )

    db.session.add_all([gq_member, dq_member1, dq_member2, w_member1, w_member2])
    db.session.commit()

    print("Seed data created:")
    print(f"  Users: raja_nir, queen_giant, queen_alpha, queen_bravo, beekeeper_demo, worker_alpha, worker_bravo")
    print(f"  Password for all: 'password'")
    print(f"  Swarm: Alpha Swarm (1 GiantQueen, 2 DwarfQueens, 2 Workers)")
    print(f"  Website: http://localhost:8877")

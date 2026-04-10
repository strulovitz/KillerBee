"""
seed_data.py — Populate KillerBee with demo data
=================================================
Run this once to create demo users, a Swarm, and members with buzzing hierarchy.

Hierarchy:
  RajaBee (swarm owner, not a member)
  └── GiantQueen (parent=None, reports to RajaBee)
      ├── DwarfQueen1 (parent=GiantQueen)
      │   └── Worker1 (parent=DwarfQueen1)
      └── DwarfQueen2 (parent=GiantQueen)
          └── Worker2 (parent=DwarfQueen2)
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

    # Add GiantQueen to the Swarm (parent=None, reports to RajaBee who is swarm owner)
    gq_member = SwarmMember(
        swarm_id=swarm.id,
        user_id=giant_queen.id,
        endpoint='http://localhost:5000',
        member_type='giant_queen',
        model_name='llama3.2:3b',
        worker_count=0,
        parent_member_id=None,
    )
    db.session.add(gq_member)
    db.session.commit()

    # Add DwarfQueens to the Swarm (parent=GiantQueen)
    dq_member1 = SwarmMember(
        swarm_id=swarm.id,
        user_id=dwarf_queen1.id,
        endpoint='http://localhost:5001',
        member_type='dwarf_queen',
        model_name='llama3.2:3b',
        worker_count=0,
        parent_member_id=gq_member.id,
    )
    dq_member2 = SwarmMember(
        swarm_id=swarm.id,
        user_id=dwarf_queen2.id,
        endpoint='http://localhost:5002',
        member_type='dwarf_queen',
        model_name='llama3.2:3b',
        worker_count=0,
        parent_member_id=gq_member.id,
    )
    db.session.add_all([dq_member1, dq_member2])
    db.session.commit()

    # Add Workers to the Swarm (each under their DwarfQueen)
    w_member1 = SwarmMember(
        swarm_id=swarm.id,
        user_id=worker1.id,
        endpoint='http://localhost:5003',
        member_type='worker',
        model_name='llama3.2:3b',
        worker_count=1,
        parent_member_id=dq_member1.id,
    )
    w_member2 = SwarmMember(
        swarm_id=swarm.id,
        user_id=worker2.id,
        endpoint='http://localhost:5004',
        member_type='worker',
        model_name='llama3.2:3b',
        worker_count=1,
        parent_member_id=dq_member2.id,
    )
    db.session.add_all([w_member1, w_member2])
    db.session.commit()

    # Set sample buzzing values (as if bosses already tested their subordinates)
    # Worker1: speed=8, quality=9 -> buzzing=72
    w_member1.buzzing_speed = 8.0
    w_member1.buzzing_quality = 9.0
    w_member1.buzzing = 72.0
    w_member1.capacity = 72.0  # leaf node: capacity = own buzzing

    # Worker2: speed=7, quality=8 -> buzzing=56
    w_member2.buzzing_speed = 7.0
    w_member2.buzzing_quality = 8.0
    w_member2.buzzing = 56.0
    w_member2.capacity = 56.0  # leaf node: capacity = own buzzing

    # DwarfQueen1: buzzing from GiantQueen's test, capacity = sum of her workers' buzzings
    dq_member1.buzzing_speed = 7.0
    dq_member1.buzzing_quality = 8.5
    dq_member1.buzzing = 59.5
    dq_member1.capacity = 72.0  # sum of Worker1's buzzing

    # DwarfQueen2: buzzing from GiantQueen's test, capacity = sum of her workers' buzzings
    dq_member2.buzzing_speed = 6.0
    dq_member2.buzzing_quality = 7.0
    dq_member2.buzzing = 42.0
    dq_member2.capacity = 56.0  # sum of Worker2's buzzing

    # GiantQueen: capacity = sum of DwarfQueens' buzzings (59.5 + 42.0 = 101.5)
    # GiantQueen's own buzzing would be set by RajaBee's test
    gq_member.buzzing_speed = 8.0
    gq_member.buzzing_quality = 9.0
    gq_member.buzzing = 72.0
    gq_member.capacity = 101.5  # sum of DwarfQueen buzzings

    # Calculate fractions
    # DwarfQueens are siblings under GiantQueen
    total_dq_capacity = dq_member1.capacity + dq_member2.capacity  # 72 + 56 = 128
    dq_member1.fraction = dq_member1.capacity / total_dq_capacity  # 72/128 = 0.5625
    dq_member2.fraction = dq_member2.capacity / total_dq_capacity  # 56/128 = 0.4375

    # Workers under DwarfQueen1 (only Worker1, so fraction=1.0)
    w_member1.fraction = 1.0

    # Workers under DwarfQueen2 (only Worker2, so fraction=1.0)
    w_member2.fraction = 1.0

    # GiantQueen is the only top-level member, so fraction=1.0
    gq_member.fraction = 1.0

    db.session.commit()

    print("Seed data created:")
    print(f"  Users: raja_nir, queen_giant, queen_alpha, queen_bravo, beekeeper_demo, worker_alpha, worker_bravo")
    print(f"  Password for all: 'password'")
    print(f"  Swarm: Alpha Swarm (1 GiantQueen + 2 DwarfQueens + 2 Workers)")
    print(f"  Hierarchy: GiantQueen -> DwarfQueen1(Worker1) + DwarfQueen2(Worker2)")
    print(f"  Buzzing scores set with sample values")
    print(f"  DwarfQueen fractions: {dq_member1.fraction:.4f} + {dq_member2.fraction:.4f} = 1.0")
    print(f"  Website: http://localhost:8877")

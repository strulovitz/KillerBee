"""smoke_multimedia_setup.py — Idempotent smoke-test setup for multimedia pipeline.

Creates users, swarm, and swarm members for the 1-process-per-tier smoke test.
Safe to run multiple times.
"""
import sys
import os
import time
import base64

# Run inside the Flask app context so we can use the ORM directly.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app import app, db
from models import User, Swarm, SwarmMember

PASSWORD = 'smoke_pass_2026'
SWARM_NAME = 'smoke_multimedia'


def make_token(user_id: int) -> str:
    raw = f"{user_id}:{int(time.time())}"
    return base64.b64encode(raw.encode()).decode()


def get_or_create_user(username, role):
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"  User '{username}' already exists (id={user.id})")
    else:
        user = User(
            username=username,
            email=f"{username}@smoke.local",
            role=role,
            is_verified=True,
            trust_score=5.0,
        )
        user.set_password(PASSWORD)
        db.session.add(user)
        db.session.commit()
        print(f"  Created user '{username}' (id={user.id}, role={role})")
    return user


def get_or_create_swarm(raja_user):
    swarm = Swarm.query.filter_by(name=SWARM_NAME).first()
    if swarm:
        print(f"  Swarm '{SWARM_NAME}' already exists (id={swarm.id})")
    else:
        swarm = Swarm(
            name=SWARM_NAME,
            description='Smoke test swarm for multimedia pipeline',
            raja_id=raja_user.id,
            raja_model='qwen3.5:9b',
            specialty='general',
            max_queens=10,
            depth=3,
        )
        db.session.add(swarm)
        db.session.commit()
        print(f"  Created swarm '{SWARM_NAME}' (id={swarm.id})")
    return swarm


def get_or_create_member(swarm, user, member_type, parent_member_id=None, endpoint='http://localhost:9000'):
    existing = SwarmMember.query.filter_by(swarm_id=swarm.id, user_id=user.id).first()
    if existing:
        print(f"  Member '{user.username}' already in swarm (member_id={existing.id})")
        # Ensure parent is correct
        if existing.parent_member_id != parent_member_id:
            existing.parent_member_id = parent_member_id
            db.session.commit()
            print(f"    Updated parent_member_id -> {parent_member_id}")
        # Ensure buzzing values are set
        if existing.buzzing is None or existing.fraction is None:
            existing.capacity = 1.0
            existing.fraction = 1.0
            existing.buzzing = 50.0
            existing.buzzing_speed = 5.0
            existing.buzzing_quality = 10.0
            db.session.commit()
            print(f"    Set buzzing values")
        return existing
    member = SwarmMember(
        swarm_id=swarm.id,
        user_id=user.id,
        parent_member_id=parent_member_id,
        endpoint=endpoint,
        member_type=member_type,
        capacity=1.0,
        fraction=1.0,
        buzzing=50.0,
        buzzing_speed=5.0,
        buzzing_quality=10.0,
    )
    db.session.add(member)
    db.session.commit()
    print(f"  Created member '{user.username}' as {member_type} (member_id={member.id}, parent={parent_member_id})")
    return member


def main():
    with app.app_context():
        print("=" * 60)
        print("  Smoke Multimedia Setup")
        print("=" * 60)

        # a. Create users
        print("\n-- Users --")
        beekeeper = get_or_create_user('smoke_beekeeper', 'beekeeper')
        raja      = get_or_create_user('smoke_raja',      'raja')
        gq        = get_or_create_user('smoke_gq',        'giant_queen')
        dq        = get_or_create_user('smoke_dq',        'dwarf_queen')
        worker    = get_or_create_user('smoke_worker',    'worker')

        # b. Create swarm
        print("\n-- Swarm --")
        swarm = get_or_create_swarm(raja)

        # c. Create members (hierarchy: raja -> gq -> dq -> worker)
        print("\n-- Members --")
        # Raja registers itself via the swarm register API during startup,
        # but we pre-create it here so topology is explicit.
        raja_member   = get_or_create_member(swarm, raja,   'raja',        parent_member_id=None)
        gq_member     = get_or_create_member(swarm, gq,     'giant_queen', parent_member_id=None)   # GQ has no parent in DB (Raja claims at runtime)
        dq_member     = get_or_create_member(swarm, dq,     'dwarf_queen', parent_member_id=gq_member.id)
        worker_member = get_or_create_member(swarm, worker, 'worker',      parent_member_id=dq_member.id)

        # d. Print summary + tokens
        print("\n" + "=" * 60)
        print("  SUMMARY")
        print("=" * 60)
        print(f"  Swarm ID:        {swarm.id}")
        print(f"  beekeeper id:    {beekeeper.id}  token: {make_token(beekeeper.id)}")
        print(f"  raja id:         {raja.id}        token: {make_token(raja.id)}")
        print(f"  gq id:           {gq.id}          token: {make_token(gq.id)}")
        print(f"  dq id:           {dq.id}          token: {make_token(dq.id)}")
        print(f"  worker id:       {worker.id}      token: {make_token(worker.id)}")
        print(f"  raja_member_id:  {raja_member.id}")
        print(f"  gq_member_id:    {gq_member.id}")
        print(f"  dq_member_id:    {dq_member.id}")
        print(f"  worker_member_id:{worker_member.id}")
        print()
        # Output machine-readable line for smoke_launch.sh
        print(f"SWARM_ID={swarm.id}")


if __name__ == '__main__':
    main()

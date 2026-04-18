"""Assign the fixed Phase 3 parent-child topology after all 15 bees register.

Eliminates the GiantQueen claim race: with 2 GiantQueens + 4 DwarfQueens, a
first-come-first-serve claim loop would let one GiantQueen grab all four
DwarfQueens. We avoid that by pre-setting parent_member_id from the
deterministic username convention:

    raja_nir
    queen_giant_a   queen_giant_b
    queen_dwarf_a1  queen_dwarf_a2   queen_dwarf_b1  queen_dwarf_b2
    worker_a1..a4                    worker_b1..b4

After this runs, each GiantQueen's _discover_and_claim_subordinates sees its
two DwarfQueens as already-assigned and skips the claim branch.

Run on the KillerBee host against the live SQLite DB. The Flask app does
not need to be stopped — SQLite handles concurrent writes, and we only
touch parent_member_id which nothing else is writing during bring-up.
"""
import argparse
import sys
import time

from app import app, db
from models import SwarmMember, User

PARENTAGE = {
    "raja_nir":        [],
    "queen_giant_a":   ["raja_nir"],
    "queen_giant_b":   ["raja_nir"],
    "queen_dwarf_a1":  ["queen_giant_a"],
    "queen_dwarf_a2":  ["queen_giant_a"],
    "queen_dwarf_b1":  ["queen_giant_b"],
    "queen_dwarf_b2":  ["queen_giant_b"],
    "worker_a1":       ["queen_dwarf_a1"],
    "worker_a2":       ["queen_dwarf_a1"],
    "worker_a3":       ["queen_dwarf_a2"],
    "worker_a4":       ["queen_dwarf_a2"],
    "worker_b1":       ["queen_dwarf_b1"],
    "worker_b2":       ["queen_dwarf_b1"],
    "worker_b3":       ["queen_dwarf_b2"],
    "worker_b4":       ["queen_dwarf_b2"],
}

EXPECTED = set(PARENTAGE.keys())


def lookup(swarm_id):
    members = {}
    rows = (
        db.session.query(SwarmMember, User)
        .join(User, SwarmMember.user_id == User.id)
        .filter(SwarmMember.swarm_id == swarm_id)
        .all()
    )
    for m, u in rows:
        members[u.username] = m
    return members


def wait_for_registration(swarm_id, timeout_s):
    deadline = time.time() + timeout_s
    last_missing = None
    while time.time() < deadline:
        members = lookup(swarm_id)
        missing = sorted(EXPECTED - set(members.keys()))
        if not missing:
            return members
        if missing != last_missing:
            print(f"  Waiting on {len(missing)} bee(s): {', '.join(missing)}")
            last_missing = missing
        time.sleep(2)
    members = lookup(swarm_id)
    missing = sorted(EXPECTED - set(members.keys()))
    print(f"TIMEOUT after {timeout_s}s. Still missing: {missing}")
    return None


def apply_topology(members):
    changes = 0
    for child_name, parents in PARENTAGE.items():
        child = members[child_name]
        if not parents:
            if child.parent_member_id is not None:
                print(f"  {child_name}: clearing parent (was {child.parent_member_id})")
                child.parent_member_id = None
                changes += 1
            continue
        parent_name = parents[0]
        parent = members[parent_name]
        if child.parent_member_id != parent.id:
            print(f"  {child_name} parent -> {parent_name} (member_id {parent.id})")
            child.parent_member_id = parent.id
            changes += 1
        else:
            print(f"  {child_name} parent already {parent_name}, skip")
    db.session.commit()
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--swarm-id", type=int, default=1)
    parser.add_argument("--wait-seconds", type=int, default=300,
                        help="Max seconds to wait for all 15 bees to register")
    args = parser.parse_args()

    with app.app_context():
        print(f"Waiting for all 15 bees to register in swarm {args.swarm_id}...")
        members = wait_for_registration(args.swarm_id, args.wait_seconds)
        if members is None:
            sys.exit(1)
        print(f"All 15 bees registered. Applying topology...")
        changes = apply_topology(members)
        print(f"Done. {changes} parent_member_id change(s) committed.")


if __name__ == "__main__":
    main()

"""
models.py — Database Models for KillerBee
==========================================
The hierarchical hive platform. Unlike BeehiveOfAI (flat: Queen + Workers),
KillerBee manages Swarms: RajaBee -> GiantQueens -> DwarfQueens -> Workers, unlimited depth.
GiantQueen = mid-level coordinator (named after Apis dorsata). No Workers directly.
DwarfQueen = lowest-level coordinator (named after Apis florea). Has Workers directly.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """A registered user — can be a Raja Bee, GiantQueen, DwarfQueen, Worker Bee, or Beekeeper.
    Roles: 'raja', 'giant_queen', 'dwarf_queen', 'worker', 'beekeeper'."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'raja', 'giant_queen', 'dwarf_queen', 'worker', 'beekeeper'
    trust_score = db.Column(db.Float, default=5.0)
    total_jobs = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    managed_swarms = db.relationship('Swarm', backref='raja', lazy=True, foreign_keys='Swarm.raja_id')
    submitted_jobs = db.relationship('SwarmJob', backref='beekeeper', lazy=True, foreign_keys='SwarmJob.beekeeper_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def display_role(self):
        roles = {
            'raja': 'Raja Bee',
            'giant_queen': 'Giant Queen',
            'dwarf_queen': 'Dwarf Queen',
            'worker': 'Worker Bee',
            'beekeeper': 'Beekeeper',
        }
        return roles.get(self.role, self.role)


class Swarm(db.Model):
    """A hierarchical hive — led by a RajaBee, containing GiantQueens and DwarfQueens.

    Unlike BeehiveOfAI's Hive (flat: 1 Queen + N Workers), a Swarm has LEVELS.
    The RajaBee at the top coordinates GiantQueens, who coordinate DwarfQueens,
    who coordinate Workers. For deeper hierarchies, a Swarm member can itself be
    another Swarm (nested). GiantQueens never have Workers directly.
    """
    __tablename__ = 'swarms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    raja_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    raja_model = db.Column(db.String(100), nullable=False)  # e.g. 'llama3.2:3b'
    specialty = db.Column(db.String(50), nullable=False, default='general')
    max_queens = db.Column(db.Integer, default=10)
    status = db.Column(db.String(20), default='active')  # 'active', 'inactive', 'full'
    trust_score = db.Column(db.Float, default=5.0)
    total_jobs_completed = db.Column(db.Integer, default=0)
    depth = db.Column(db.Integer, default=2)  # hierarchy depth: 2 = Raja->DwarfQueen->Worker, 3 = Raja->GiantQueen->DwarfQueen->Worker
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    members = db.relationship('SwarmMember', backref='swarm', lazy=True)
    jobs = db.relationship('SwarmJob', backref='swarm', lazy=True)

    @property
    def giant_queen_count(self):
        return SwarmMember.query.filter_by(swarm_id=self.id, member_type='giant_queen', status='active').count()

    @property
    def dwarf_queen_count(self):
        return SwarmMember.query.filter_by(swarm_id=self.id, member_type='dwarf_queen', status='active').count()

    @property
    def queen_count(self):
        return self.giant_queen_count + self.dwarf_queen_count

    @property
    def total_workers(self):
        return SwarmMember.query.filter_by(swarm_id=self.id, member_type='worker', status='active').count()

    @property
    def is_full(self):
        return self.queen_count >= self.max_queens


class SwarmMember(db.Model):
    """A GiantQueen, DwarfQueen, or nested RajaBee that belongs to a Swarm.

    GiantQueens coordinate DwarfQueens (no Workers directly).
    DwarfQueens coordinate Workers (lowest level).
    Each member reports its capabilities (worker count, model, etc.) via the
    Report Up pattern. The Swarm uses this for proportional work distribution.
    """
    __tablename__ = 'swarm_members'

    id = db.Column(db.Integer, primary_key=True)
    swarm_id = db.Column(db.Integer, db.ForeignKey('swarms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_member_id = db.Column(db.Integer, db.ForeignKey('swarm_members.id'), nullable=True)
    endpoint = db.Column(db.String(200), nullable=False)  # e.g. 'http://192.168.1.100:5000'
    member_type = db.Column(db.String(20), nullable=False, default='dwarf_queen')  # 'giant_queen', 'dwarf_queen', or 'worker'
    model_name = db.Column(db.String(100), nullable=True)
    worker_count = db.Column(db.Integer, default=1)
    avg_response_time = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')  # 'active', 'inactive', 'offline'
    last_heartbeat = db.Column(db.DateTime, nullable=True)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Buzzing performance system — boss tests employee, calculates scores
    buzzing_speed = db.Column(db.Float, nullable=True)    # 1-10, set by boss
    buzzing_quality = db.Column(db.Float, nullable=True)  # 1-10, set by boss
    buzzing = db.Column(db.Float, nullable=True)           # speed * quality, 1-100
    capacity = db.Column(db.Float, nullable=True)          # sum of subordinate buzzings (or own buzzing for workers)
    fraction = db.Column(db.Float, nullable=True)          # capacity / total among siblings, sums to 1

    # Relationships
    user = db.relationship('User', backref='swarm_memberships')
    subordinates = db.relationship('SwarmMember', backref=db.backref('parent_member', remote_side=[id]), lazy=True)


class SwarmJob(db.Model):
    """A task submitted to a Swarm for hierarchical processing."""
    __tablename__ = 'swarm_jobs'

    id = db.Column(db.Integer, primary_key=True)
    swarm_id = db.Column(db.Integer, db.ForeignKey('swarms.id'), nullable=False)
    beekeeper_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task = db.Column(db.Text, nullable=False)
    result = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'splitting', 'processing', 'combining', 'completed', 'failed'
    components_total = db.Column(db.Integer, default=0)
    components_completed = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Float, nullable=True)
    depth_used = db.Column(db.Integer, nullable=True)  # actual hierarchy depth used
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    # Track which components went to which members
    components = db.relationship('JobComponent', backref='job', lazy=True)


class JobComponent(db.Model):
    """A piece of a job assigned to a specific Swarm member (GiantQueen, DwarfQueen, or Worker).

    Recursive: components can have child components (parent_id).
    - RajaBee splits job -> top-level components (parent_id=None, level=0)
    - GiantQueen splits her component -> child components (level=1)
    - DwarfQueen splits her component -> subtask components (level=2)
    - Worker processes a subtask component
    """
    __tablename__ = 'job_components'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('swarm_jobs.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('swarm_members.id'), nullable=True)  # nullable: starts unassigned
    parent_id = db.Column(db.Integer, db.ForeignKey('job_components.id'), nullable=True)  # None = top-level
    task_description = db.Column(db.Text, nullable=False)
    result = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    level = db.Column(db.Integer, default=0)  # 0=from RajaBee, 1=from GiantQueen, 2=from DwarfQueen
    component_type = db.Column(db.String(20), default='component')  # 'component' or 'subtask'
    processing_time = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    member = db.relationship('SwarmMember', backref='components')
    children = db.relationship('JobComponent', backref=db.backref('parent', remote_side=[id]), lazy=True)

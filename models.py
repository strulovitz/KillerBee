"""
models.py — Database Models for KillerBee
==========================================
The hierarchical hive platform. Unlike BeehiveOfAI (flat: Queen + Workers),
KillerBee manages Swarms: RajaBee → Queens → Workers, unlimited depth.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """A registered user — can be a Raja Bee, Queen Bee, Worker Bee, or Beekeeper."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'raja', 'queen', 'worker', 'beekeeper'
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
            'queen': 'Queen Bee',
            'worker': 'Worker Bee',
            'beekeeper': 'Beekeeper',
        }
        return roles.get(self.role, self.role)


class Swarm(db.Model):
    """A hierarchical hive — led by a RajaBee, containing Queens (each with Workers).

    Unlike BeehiveOfAI's Hive (flat: 1 Queen + N Workers), a Swarm has LEVELS.
    The RajaBee at the top coordinates Queens, who coordinate Workers.
    For deeper hierarchies, a Swarm member can itself be another Swarm (nested).
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
    depth = db.Column(db.Integer, default=2)  # hierarchy depth: 2 = Raja→Queen→Worker, 3 = Raja→Raja→Queen→Worker
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    members = db.relationship('SwarmMember', backref='swarm', lazy=True)
    jobs = db.relationship('SwarmJob', backref='swarm', lazy=True)

    @property
    def queen_count(self):
        return SwarmMember.query.filter_by(swarm_id=self.id, status='active').count()

    @property
    def total_workers(self):
        """Total workers across all Queens in this Swarm."""
        return sum(m.worker_count for m in self.members if m.status == 'active')

    @property
    def is_full(self):
        return self.queen_count >= self.max_queens


class SwarmMember(db.Model):
    """A Queen (or nested RajaBee) that belongs to a Swarm.

    Each member reports its capabilities (worker count, model, etc.) via the
    Report Up pattern. The Swarm uses this for proportional work distribution.
    """
    __tablename__ = 'swarm_members'

    id = db.Column(db.Integer, primary_key=True)
    swarm_id = db.Column(db.Integer, db.ForeignKey('swarms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint = db.Column(db.String(200), nullable=False)  # e.g. 'http://192.168.1.100:5000'
    member_type = db.Column(db.String(20), nullable=False, default='queen')  # 'queen' or 'raja'
    model_name = db.Column(db.String(100), nullable=True)
    worker_count = db.Column(db.Integer, default=1)
    avg_response_time = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')  # 'active', 'inactive', 'offline'
    last_heartbeat = db.Column(db.DateTime, nullable=True)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    user = db.relationship('User', backref='swarm_memberships')


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
    """A piece of a job assigned to a specific Swarm member (Queen or nested RajaBee)."""
    __tablename__ = 'job_components'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('swarm_jobs.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('swarm_members.id'), nullable=False)
    task_description = db.Column(db.Text, nullable=False)
    result = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    processing_time = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    member = db.relationship('SwarmMember', backref='components')

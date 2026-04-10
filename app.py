"""
app.py — Main Flask Application for KillerBee
===============================================
The hierarchical hive platform. Manages Swarms: RajaBee -> GiantQueens -> DwarfQueens -> Workers.
GiantQueen = mid-level coordinator (no Workers directly, coordinates DwarfQueens).
DwarfQueen = lowest-level coordinator (has Workers directly under her).
DB role 'queen' covers both types; display text distinguishes them.
"""

import os
from datetime import datetime, timezone
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from models import db, User, Swarm, SwarmMember, SwarmJob, JobComponent
from forms import RegisterForm, LoginForm, CreateSwarmForm, JoinSwarmForm, SubmitJobForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('KILLERBEE_SECRET_KEY', 'dev-only-secret-key-not-for-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///killerbee.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ── Role decorators ──────────────────────────────────────────────────────────

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('You do not have permission to access that page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── Public pages ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    swarms = Swarm.query.filter_by(status='active').order_by(Swarm.total_jobs_completed.desc()).all()
    stats = {
        'total_swarms': Swarm.query.count(),
        'total_users': User.query.count(),
        'total_jobs': SwarmJob.query.count(),
        'total_queens': SwarmMember.query.filter_by(status='active').count(),  # GiantQueens + DwarfQueens
    }
    return render_template('index.html', swarms=swarms, stats=stats)


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html', form=form)
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome to KillerBee, {user.username}!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'raja':
        swarms = Swarm.query.filter_by(raja_id=current_user.id).all()
        return render_template('dashboard_raja.html', swarms=swarms)
    elif current_user.role == 'queen':
        memberships = SwarmMember.query.filter_by(user_id=current_user.id).all()
        available_swarms = Swarm.query.filter_by(status='active').all()
        return render_template('dashboard_queen.html', memberships=memberships, available_swarms=available_swarms)
    elif current_user.role == 'beekeeper':
        jobs = SwarmJob.query.filter_by(beekeeper_id=current_user.id).order_by(SwarmJob.created_at.desc()).all()
        swarms = Swarm.query.filter_by(status='active').all()
        return render_template('dashboard_beekeeper.html', jobs=jobs, swarms=swarms)
    else:
        return render_template('dashboard_worker.html')


# ── Swarm management (Raja Bee) ──────────────────────────────────────────────

@app.route('/swarm/create', methods=['GET', 'POST'])
@login_required
@role_required('raja')
def create_swarm():
    form = CreateSwarmForm()
    if form.validate_on_submit():
        if Swarm.query.filter_by(name=form.name.data).first():
            flash('Swarm name already taken.', 'danger')
            return render_template('create_swarm.html', form=form)
        swarm = Swarm(
            name=form.name.data,
            description=form.description.data,
            raja_id=current_user.id,
            raja_model=form.raja_model.data,
            specialty=form.specialty.data,
            max_queens=form.max_queens.data,
        )
        db.session.add(swarm)
        db.session.commit()
        flash(f'Swarm "{swarm.name}" created!', 'success')
        return redirect(url_for('view_swarm', swarm_id=swarm.id))
    return render_template('create_swarm.html', form=form)


@app.route('/swarm/<int:swarm_id>')
def view_swarm(swarm_id):
    swarm = Swarm.query.get_or_404(swarm_id)
    members = SwarmMember.query.filter_by(swarm_id=swarm.id).all()
    recent_jobs = SwarmJob.query.filter_by(swarm_id=swarm.id).order_by(SwarmJob.created_at.desc()).limit(10).all()
    return render_template('view_swarm.html', swarm=swarm, members=members, recent_jobs=recent_jobs)


# ── Join Swarm (GiantQueen / DwarfQueen) ─────────────────────────────────────

@app.route('/swarm/<int:swarm_id>/join', methods=['GET', 'POST'])
@login_required
@role_required('queen')
def join_swarm(swarm_id):
    swarm = Swarm.query.get_or_404(swarm_id)
    if swarm.is_full:
        flash('This Swarm is full.', 'warning')
        return redirect(url_for('view_swarm', swarm_id=swarm.id))

    form = JoinSwarmForm()
    if form.validate_on_submit():
        existing = SwarmMember.query.filter_by(swarm_id=swarm.id, user_id=current_user.id).first()
        if existing:
            flash('You are already in this Swarm.', 'warning')
            return redirect(url_for('view_swarm', swarm_id=swarm.id))

        member = SwarmMember(
            swarm_id=swarm.id,
            user_id=current_user.id,
            endpoint=form.endpoint.data,
            member_type='queen',
        )
        db.session.add(member)
        db.session.commit()
        flash(f'Joined Swarm "{swarm.name}"!', 'success')
        return redirect(url_for('view_swarm', swarm_id=swarm.id))
    return render_template('join_swarm.html', swarm=swarm, form=form)


# ── Submit Job (Beekeeper) ────────────────────────────────────────────────────

@app.route('/swarm/<int:swarm_id>/submit', methods=['GET', 'POST'])
@login_required
@role_required('beekeeper')
def submit_job(swarm_id):
    swarm = Swarm.query.get_or_404(swarm_id)
    form = SubmitJobForm()
    if form.validate_on_submit():
        job = SwarmJob(
            swarm_id=swarm.id,
            beekeeper_id=current_user.id,
            task=form.task.data,
        )
        db.session.add(job)
        db.session.commit()
        flash(f'Job submitted to Swarm "{swarm.name}"!', 'success')
        return redirect(url_for('view_job', job_id=job.id))
    return render_template('submit_job.html', swarm=swarm, form=form)


@app.route('/job/<int:job_id>')
@login_required
def view_job(job_id):
    job = SwarmJob.query.get_or_404(job_id)
    components = JobComponent.query.filter_by(job_id=job.id).all()
    return render_template('view_job.html', job=job, components=components)


# ── API endpoints (for RajaBee client to interact) ───────────────────────────

@app.route('/api/swarm/<int:swarm_id>/members', methods=['GET'])
@csrf.exempt
def api_swarm_members(swarm_id):
    """Return all active members (GiantQueens/DwarfQueens) of a Swarm — used by RajaBee client."""
    swarm = Swarm.query.get_or_404(swarm_id)
    members = SwarmMember.query.filter_by(swarm_id=swarm.id, status='active').all()
    return jsonify({
        'swarm': swarm.name,
        'raja_model': swarm.raja_model,
        'members': [{
            'id': m.id,
            'endpoint': m.endpoint,
            'type': m.member_type,
            'model': m.model_name,
            'workers': m.worker_count,
            'avg_response_time': m.avg_response_time,
        } for m in members]
    })


@app.route('/api/swarm/<int:swarm_id>/heartbeat', methods=['POST'])
@csrf.exempt
def api_heartbeat(swarm_id):
    """GiantQueen/DwarfQueen reports she's still alive + updated capabilities."""
    data = request.get_json()
    endpoint = data.get('endpoint')
    member = SwarmMember.query.filter_by(swarm_id=swarm_id, endpoint=endpoint).first()
    if not member:
        return jsonify({'error': 'Not a member of this swarm'}), 404

    member.last_heartbeat = datetime.now(timezone.utc)
    member.worker_count = data.get('workers', member.worker_count)
    member.model_name = data.get('model', member.model_name)
    member.avg_response_time = data.get('avg_response_time', member.avg_response_time)
    db.session.commit()
    return jsonify({'status': 'ok'})


@app.route('/api/job/<int:job_id>/update', methods=['POST'])
@csrf.exempt
def api_job_update(job_id):
    """RajaBee reports job progress or completion."""
    data = request.get_json()
    job = SwarmJob.query.get_or_404(job_id)

    if 'status' in data:
        job.status = data['status']
    if 'result' in data:
        job.result = data['result']
    if 'total_time' in data:
        job.total_time = data['total_time']
    if 'depth_used' in data:
        job.depth_used = data['depth_used']
    if 'components_completed' in data:
        job.components_completed = data['components_completed']
    if data.get('status') == 'completed':
        job.completed_at = datetime.now(timezone.utc)
        swarm = Swarm.query.get(job.swarm_id)
        swarm.total_jobs_completed += 1

    db.session.commit()
    return jsonify({'status': 'ok'})


# ── Init DB ───────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8877, debug=True)

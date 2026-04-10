"""
app.py — Main Flask Application for KillerBee
===============================================
The hierarchical hive platform. Manages Swarms: RajaBee -> GiantQueens -> DwarfQueens -> Workers.
GiantQueen = mid-level coordinator (no Workers directly, coordinates DwarfQueens).
DwarfQueen = lowest-level coordinator (has Workers directly under her).
Roles: 'raja', 'giant_queen', 'dwarf_queen', 'worker', 'beekeeper'.
"""

import os
import base64
import time
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
    elif current_user.role in ('giant_queen', 'dwarf_queen'):
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
@role_required('giant_queen', 'dwarf_queen')
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
            member_type=current_user.role,  # 'giant_queen' or 'dwarf_queen'
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
    # Get ALL components including nested subtasks, ordered by level then ID
    components = JobComponent.query.filter_by(job_id=job.id).order_by(
        JobComponent.parent_id.nullsfirst(), JobComponent.level, JobComponent.id
    ).all()
    return render_template('view_job.html', job=job, components=components)


@app.route('/job/<int:job_id>/live')
def view_job_live(job_id):
    """Public live view of a job — no login required, auto-refreshes."""
    job = SwarmJob.query.get_or_404(job_id)
    components = JobComponent.query.filter_by(job_id=job.id).order_by(
        JobComponent.parent_id.nullsfirst(), JobComponent.level, JobComponent.id
    ).all()
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


# ── Token helpers ────────────────────────────────────────────────────────────

def make_token(user_id):
    """Simple base64 token: user_id:timestamp. Good enough for now."""
    raw = f"{user_id}:{int(time.time())}"
    return base64.b64encode(raw.encode()).decode()


def verify_token(token):
    """Decode token, return user_id or None."""
    try:
        raw = base64.b64decode(token.encode()).decode()
        user_id_str = raw.split(':')[0]
        return int(user_id_str)
    except Exception:
        return None


def get_api_user():
    """Extract user from Authorization header (Bearer token). Returns User or None."""
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth[7:]
        user_id = verify_token(token)
        if user_id:
            return db.session.get(User, user_id)
    return None


# ── Auth API ─────────────────────────────────────────────────────────────────

@app.route('/api/auth/login', methods=['POST'])
@csrf.exempt
def api_auth_login():
    """Authenticate and receive a token for API access."""
    data = request.get_json()
    if not data:
        return jsonify({'ok': False, 'error': 'JSON body required'}), 400
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'ok': False, 'error': 'username and password required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'ok': False, 'error': 'Invalid credentials'}), 401

    token = make_token(user.id)
    return jsonify({'ok': True, 'user_id': user.id, 'role': user.role, 'token': token})


# ── Job Workflow API (RajaBee) ───────────────────────────────────────────────

@app.route('/api/swarm/<int:swarm_id>/jobs/pending', methods=['GET'])
@csrf.exempt
def api_pending_jobs(swarm_id):
    """Return pending jobs for this swarm — used by RajaBee to find work."""
    swarm = Swarm.query.get_or_404(swarm_id)
    jobs = SwarmJob.query.filter_by(swarm_id=swarm.id, status='pending').all()
    return jsonify({
        'swarm_id': swarm.id,
        'jobs': [{
            'id': j.id,
            'task': j.task,
            'status': j.status,
            'created_at': j.created_at.isoformat(),
        } for j in jobs]
    })


@app.route('/api/job/<int:job_id>/split', methods=['POST'])
@csrf.exempt
def api_job_split(job_id):
    """RajaBee splits a job into top-level components."""
    data = request.get_json()
    if not data or 'components' not in data:
        return jsonify({'error': 'components list required'}), 400

    job = SwarmJob.query.get_or_404(job_id)
    job.status = 'splitting'

    created = []
    for comp_data in data['components']:
        member_id = comp_data.get('assigned_member_id')  # can be None
        comp = JobComponent(
            job_id=job.id,
            member_id=member_id,
            parent_id=None,  # top-level
            task_description=comp_data['task'],
            level=0,
            component_type='component',
        )
        db.session.add(comp)
        created.append(comp)

    job.components_total = len(created)
    job.status = 'processing'
    db.session.commit()

    return jsonify({
        'ok': True,
        'job_id': job.id,
        'components': [{'id': c.id, 'task': c.task_description, 'member_id': c.member_id} for c in created]
    })


@app.route('/api/job/<int:job_id>/result', methods=['POST'])
@csrf.exempt
def api_job_result(job_id):
    """RajaBee posts the final combined result for a job."""
    data = request.get_json()
    if not data or 'result' not in data:
        return jsonify({'error': 'result required'}), 400

    job = SwarmJob.query.get_or_404(job_id)
    job.result = data['result']
    job.total_time = data.get('total_time')
    job.status = 'completed'
    job.completed_at = datetime.now(timezone.utc)

    swarm = Swarm.query.get(job.swarm_id)
    swarm.total_jobs_completed += 1

    db.session.commit()
    return jsonify({'ok': True, 'job_id': job.id})


# ── Component Workflow API (GiantQueens, DwarfQueens, Workers) ───────────────

@app.route('/api/member/<int:member_id>/work', methods=['GET'])
@csrf.exempt
def api_member_work(member_id):
    """Return components assigned to this member that need processing."""
    member = SwarmMember.query.get_or_404(member_id)
    components = JobComponent.query.filter_by(
        member_id=member.id, status='pending'
    ).all()
    return jsonify({
        'member_id': member.id,
        'components': [{
            'id': c.id,
            'job_id': c.job_id,
            'task': c.task_description,
            'level': c.level,
            'component_type': c.component_type,
            'parent_id': c.parent_id,
            'status': c.status,
        } for c in components]
    })


@app.route('/api/component/<int:component_id>/claim', methods=['POST'])
@csrf.exempt
def api_component_claim(component_id):
    """Claim an unclaimed component."""
    data = request.get_json()
    if not data or 'member_id' not in data:
        return jsonify({'error': 'member_id required'}), 400

    comp = JobComponent.query.get_or_404(component_id)
    if comp.member_id is not None:
        return jsonify({'error': 'Component already claimed', 'claimed_by': comp.member_id}), 409

    member = SwarmMember.query.get_or_404(data['member_id'])
    comp.member_id = member.id
    comp.status = 'processing'
    db.session.commit()

    return jsonify({
        'ok': True,
        'component_id': comp.id,
        'member_id': member.id,
        'task': comp.task_description,
    })


@app.route('/api/component/<int:component_id>/split', methods=['POST'])
@csrf.exempt
def api_component_split(component_id):
    """Queen splits her component into child components/subtasks."""
    data = request.get_json()
    if not data or 'children' not in data:
        return jsonify({'error': 'children list required'}), 400

    parent = JobComponent.query.get_or_404(component_id)
    parent.status = 'processing'

    created = []
    for child_data in data['children']:
        child = JobComponent(
            job_id=parent.job_id,
            member_id=child_data.get('assigned_member_id'),  # can be None (unclaimed)
            parent_id=parent.id,
            task_description=child_data['task'],
            level=parent.level + 1,
            component_type=child_data.get('component_type', 'component'),
        )
        db.session.add(child)
        created.append(child)

    db.session.commit()

    return jsonify({
        'ok': True,
        'parent_id': parent.id,
        'children': [{'id': c.id, 'task': c.task_description, 'level': c.level, 'component_type': c.component_type} for c in created]
    })


@app.route('/api/component/<int:component_id>/children', methods=['GET'])
@csrf.exempt
def api_component_children(component_id):
    """Return child components and their statuses/results."""
    parent = JobComponent.query.get_or_404(component_id)
    children = JobComponent.query.filter_by(parent_id=parent.id).all()
    return jsonify({
        'parent_id': parent.id,
        'children': [{
            'id': c.id,
            'task': c.task_description,
            'status': c.status,
            'result': c.result,
            'level': c.level,
            'component_type': c.component_type,
            'member_id': c.member_id,
            'processing_time': c.processing_time,
        } for c in children]
    })


@app.route('/api/component/<int:component_id>/status', methods=['GET'])
@csrf.exempt
def api_component_status(component_id):
    """Return the status and result of a single component."""
    comp = JobComponent.query.get_or_404(component_id)
    return jsonify({
        'id': comp.id,
        'job_id': comp.job_id,
        'task': comp.task_description,
        'status': comp.status,
        'result': comp.result,
        'level': comp.level,
        'component_type': comp.component_type,
        'member_id': comp.member_id,
        'processing_time': comp.processing_time,
        'parent_id': comp.parent_id,
    })


@app.route('/api/component/<int:component_id>/result', methods=['POST'])
@csrf.exempt
def api_component_result(component_id):
    """Worker posts subtask result, or Queen posts combined result."""
    data = request.get_json()
    if not data or 'result' not in data:
        return jsonify({'error': 'result required'}), 400

    comp = JobComponent.query.get_or_404(component_id)
    comp.result = data['result']
    comp.processing_time = data.get('processing_time')
    comp.status = 'completed'
    db.session.commit()

    return jsonify({'ok': True, 'component_id': comp.id})


@app.route('/api/swarm/<int:swarm_id>/subtasks/available', methods=['GET'])
@csrf.exempt
def api_available_subtasks(swarm_id):
    """Return unclaimed subtask components for Workers to claim."""
    swarm = Swarm.query.get_or_404(swarm_id)
    # Get all jobs in this swarm, then find unclaimed subtasks
    job_ids = [j.id for j in SwarmJob.query.filter_by(swarm_id=swarm.id).all()]
    subtasks = JobComponent.query.filter(
        JobComponent.job_id.in_(job_ids),
        JobComponent.component_type == 'subtask',
        JobComponent.member_id.is_(None),
        JobComponent.status == 'pending',
    ).all() if job_ids else []

    return jsonify({
        'swarm_id': swarm.id,
        'subtasks': [{
            'id': s.id,
            'job_id': s.job_id,
            'task': s.task_description,
            'level': s.level,
            'parent_id': s.parent_id,
        } for s in subtasks]
    })


@app.route('/api/swarm/<int:swarm_id>/components/available', methods=['GET'])
@csrf.exempt
def api_available_components(swarm_id):
    """Return unclaimed non-subtask components for GiantQueens/DwarfQueens to claim."""
    swarm = Swarm.query.get_or_404(swarm_id)
    job_ids = [j.id for j in SwarmJob.query.filter_by(swarm_id=swarm.id, status='processing').all()]
    components = JobComponent.query.filter(
        JobComponent.job_id.in_(job_ids),
        JobComponent.component_type == 'component',
        JobComponent.member_id.is_(None),
        JobComponent.status == 'pending',
    ).all() if job_ids else []

    return jsonify({
        'swarm_id': swarm.id,
        'components': [{
            'id': c.id,
            'job_id': c.job_id,
            'task': c.task_description,
            'level': c.level,
            'parent_id': c.parent_id,
        } for c in components]
    })


# ── Member Registration API ─────────────────────────────────────────────────

@app.route('/api/swarm/<int:swarm_id>/register', methods=['POST'])
@csrf.exempt
def api_swarm_register(swarm_id):
    """Register a new user and join a swarm programmatically (for CLI clients)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    username = data.get('username')
    password = data.get('password')
    member_type = data.get('member_type', 'worker')
    model = data.get('model')

    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400

    if member_type not in ('giant_queen', 'dwarf_queen', 'worker'):
        return jsonify({'error': 'member_type must be giant_queen, dwarf_queen, or worker'}), 400

    swarm = Swarm.query.get_or_404(swarm_id)

    # Create or find user
    user = User.query.filter_by(username=username).first()
    if user:
        if not user.check_password(password):
            return jsonify({'error': 'Invalid credentials for existing user'}), 401
    else:
        # Map member_type to user role
        user = User(
            username=username,
            email=f"{username}@killerbee.local",
            role=member_type,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

    # Check if already a member
    existing = SwarmMember.query.filter_by(swarm_id=swarm.id, user_id=user.id).first()
    if existing:
        token = make_token(user.id)
        return jsonify({
            'ok': True, 'user_id': user.id, 'member_id': existing.id,
            'token': token, 'message': 'Already a member'
        })

    member = SwarmMember(
        swarm_id=swarm.id,
        user_id=user.id,
        endpoint=data.get('endpoint', 'http://localhost:0'),
        member_type=member_type,
        model_name=model,
        worker_count=data.get('worker_count', 1),
    )
    db.session.add(member)
    db.session.commit()

    token = make_token(user.id)
    return jsonify({
        'ok': True, 'user_id': user.id, 'member_id': member.id, 'token': token,
    })


# ── Init DB ───────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8877, debug=True)

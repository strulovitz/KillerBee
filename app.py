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
import shutil
import subprocess
import time
from datetime import datetime, timezone
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from werkzeug.utils import secure_filename, safe_join
from models import db, User, Swarm, SwarmMember, SwarmJob, JobComponent
from forms import RegisterForm, LoginForm, CreateSwarmForm, JoinSwarmForm, SubmitJobForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('KILLERBEE_SECRET_KEY', 'dev-only-secret-key-not-for-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///killerbee.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB cap for video uploads

# Multimedia uploads root — sub-folders: photo/, audio/, video/
UPLOADS_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOADS_ROOT, exist_ok=True)

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
        media_type = form.media_type.data  # 'text' | 'photo' | 'audio' | 'video'

        job = SwarmJob(
            swarm_id=swarm.id,
            beekeeper_id=current_user.id,
            task=form.task.data,
            media_type=media_type if media_type != 'text' else None,
        )
        db.session.add(job)
        db.session.flush()  # get job.id before commit

        if media_type != 'text' and form.media_file.data:
            uploaded = form.media_file.data
            original_filename = secure_filename(uploaded.filename)
            ext = os.path.splitext(original_filename)[1].lower()  # e.g. '.jpg'
            if not ext:
                ext = {'photo': '.jpg', 'audio': '.mp3', 'video': '.mp4'}[media_type]

            # Save to uploads/<media_type>/swarmjob_<id>/original<ext>
            job_folder = os.path.join(UPLOADS_ROOT, media_type, f'swarmjob_{job.id}')
            os.makedirs(job_folder, exist_ok=True)
            original_path = os.path.join(job_folder, f'original{ext}')
            uploaded.save(original_path)

            # Server-relative URL (used by GiantHoneyBee clients to fetch)
            media_url = f'{media_type}/swarmjob_{job.id}/original{ext}'
            job.media_url = media_url

            # For video: extract audio track via ffmpeg
            if media_type == 'video':
                audio_path = os.path.join(job_folder, 'original_audio.mp3')
                try:
                    result = subprocess.run(
                        ['ffmpeg', '-y', '-i', original_path,
                         '-vn', '-acodec', 'libmp3lame', audio_path],
                        capture_output=True, timeout=120,
                    )
                    if result.returncode != 0:
                        app.logger.warning(
                            f'ffmpeg audio extract failed for job {job.id}: '
                            f'{result.stderr.decode(errors="replace")}'
                        )
                except FileNotFoundError:
                    # TODO: make ffmpeg a hard requirement before production
                    app.logger.warning(
                        f'ffmpeg not found — skipping audio track extraction for job {job.id}'
                    )
                except subprocess.TimeoutExpired:
                    app.logger.warning(
                        f'ffmpeg audio extract timed out for job {job.id}'
                    )

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

    # Cleanup uploaded media files now that the job is complete (Section 12)
    if job.media_type:
        media_folder = os.path.join(UPLOADS_ROOT, job.media_type, f'swarmjob_{job.id}')
        if os.path.isdir(media_folder):
            try:
                shutil.rmtree(media_folder)
                app.logger.info(f'Cleaned up media folder: {media_folder}')
            except Exception as exc:
                app.logger.warning(f'Failed to clean up {media_folder}: {exc}')

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
            'original_task': c.job.task,
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
            'original_task': s.job.task,
            'level': s.level,
            'parent_id': s.parent_id,
        } for s in subtasks]
    })


@app.route('/api/swarm/<int:swarm_id>/components/available', methods=['GET'])
@csrf.exempt
def api_available_components(swarm_id):
    """Return unclaimed non-subtask components for GiantQueens/DwarfQueens to claim."""
    swarm = Swarm.query.get_or_404(swarm_id)
    job_ids = [j.id for j in SwarmJob.query.filter_by(swarm_id=swarm.id).all()]
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
            'original_task': c.job.task,
            'level': c.level,
            'parent_id': c.parent_id,
        } for c in components]
    })


# ── Calibration API ─────────────────────────────────────────────────────────

@app.route('/api/member/<int:member_id>/calibration', methods=['POST'])
@csrf.exempt
def api_member_calibration(member_id):
    """Boss sends a calibration task to a subordinate. Creates a special component assigned to them."""
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({'error': 'task required'}), 400

    member = SwarmMember.query.get_or_404(member_id)

    # Find any active job in this swarm to attach the calibration to,
    # or create a special calibration job
    swarm = Swarm.query.get(member.swarm_id)
    cal_job = SwarmJob.query.filter_by(swarm_id=swarm.id, status='calibration').first()
    if not cal_job:
        cal_job = SwarmJob(
            swarm_id=swarm.id,
            beekeeper_id=swarm.raja_id,
            task='[CALIBRATION] Buzzing performance test',
            status='calibration'
        )
        db.session.add(cal_job)
        db.session.commit()

    # Create a calibration component assigned to this member
    comp = JobComponent(
        job_id=cal_job.id,
        member_id=member.id,
        parent_id=None,
        task_description=data['task'],
        level=0,
        component_type=data.get('component_type', 'calibration'),
        status='pending',
    )
    db.session.add(comp)
    db.session.commit()

    return jsonify({
        'ok': True,
        'component_id': comp.id,
        'member_id': member.id,
        'task': comp.task_description,
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

    if member_type not in ('raja', 'giant_queen', 'dwarf_queen', 'worker'):
        return jsonify({'error': 'member_type must be raja, giant_queen, dwarf_queen, or worker'}), 400

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
        parent_member_id=data.get('parent_member_id'),
    )
    db.session.add(member)
    db.session.commit()

    token = make_token(user.id)
    return jsonify({
        'ok': True, 'user_id': user.id, 'member_id': member.id, 'token': token,
    })


# ── Buzzing Performance System API ──────────────────────────────────────────

@app.route('/api/member/<int:member_id>/subordinates', methods=['GET'])
@csrf.exempt
def api_member_subordinates(member_id):
    """Return subordinates of this member (members whose parent_member_id = this member)."""
    member = SwarmMember.query.get_or_404(member_id)
    subs = SwarmMember.query.filter_by(parent_member_id=member.id).all()
    return jsonify({
        'member_id': member.id,
        'subordinates': [{
            'id': s.id,
            'username': s.user.username,
            'member_type': s.member_type,
            'model_name': s.model_name,
            'buzzing': s.buzzing,
            'fraction': s.fraction,
            'status': s.status,
        } for s in subs]
    })


@app.route('/api/swarm/<int:swarm_id>/unassigned', methods=['GET'])
@csrf.exempt
def api_swarm_unassigned(swarm_id):
    """Return members with no parent_member_id (available to be claimed by a boss)."""
    swarm = Swarm.query.get_or_404(swarm_id)
    query = SwarmMember.query.filter_by(swarm_id=swarm.id, parent_member_id=None)

    member_type = request.args.get('type')
    if member_type:
        query = query.filter_by(member_type=member_type)

    members = query.all()
    return jsonify({
        'swarm_id': swarm.id,
        'unassigned': [{
            'id': m.id,
            'username': m.user.username,
            'member_type': m.member_type,
            'model_name': m.model_name,
            'endpoint': m.endpoint,
            'status': m.status,
        } for m in members]
    })


@app.route('/api/member/<int:member_id>/claim-subordinate', methods=['POST'])
@csrf.exempt
def api_claim_subordinate(member_id):
    """Boss claims a subordinate — sets subordinate's parent_member_id to this member."""
    data = request.get_json()
    if not data or 'subordinate_member_id' not in data:
        return jsonify({'error': 'subordinate_member_id required'}), 400

    boss = SwarmMember.query.get_or_404(member_id)
    sub = SwarmMember.query.get_or_404(data['subordinate_member_id'])

    if sub.parent_member_id is not None:
        return jsonify({'error': 'Subordinate already has a boss', 'current_boss': sub.parent_member_id}), 409

    if sub.swarm_id != boss.swarm_id:
        return jsonify({'error': 'Subordinate is not in the same swarm'}), 400

    sub.parent_member_id = boss.id
    db.session.commit()

    return jsonify({
        'ok': True,
        'boss_id': boss.id,
        'subordinate': {
            'id': sub.id,
            'username': sub.user.username,
            'member_type': sub.member_type,
            'model_name': sub.model_name,
        }
    })


@app.route('/api/member/<int:member_id>/buzzing', methods=['POST'])
@csrf.exempt
def api_member_buzzing(member_id):
    """Boss reports a subordinate's buzzing score (speed x quality)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    required = ['buzzing_speed', 'buzzing_quality', 'reporter_member_id']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} required'}), 400

    member = SwarmMember.query.get_or_404(member_id)
    reporter_id = data['reporter_member_id']

    # Verify the reporter is this member's boss
    if member.parent_member_id != reporter_id:
        return jsonify({'error': 'Only the parent (boss) can report buzzing scores'}), 403

    speed = float(data['buzzing_speed'])
    quality = float(data['buzzing_quality'])

    if not (1 <= speed <= 10) or not (1 <= quality <= 10):
        return jsonify({'error': 'buzzing_speed and buzzing_quality must be between 1 and 10'}), 400

    member.buzzing_speed = speed
    member.buzzing_quality = quality
    member.buzzing = speed * quality
    db.session.commit()

    return jsonify({
        'ok': True,
        'member_id': member.id,
        'buzzing_speed': member.buzzing_speed,
        'buzzing_quality': member.buzzing_quality,
        'buzzing': member.buzzing,
    })


@app.route('/api/member/<int:member_id>/recalculate', methods=['POST'])
@csrf.exempt
def api_member_recalculate(member_id):
    """Recalculate this member's capacity and all sibling fractions."""
    member = SwarmMember.query.get_or_404(member_id)

    # First: recalculate fractions among this member's SUBORDINATES
    subs = SwarmMember.query.filter_by(parent_member_id=member.id).all()
    if subs:
        # Set each subordinate's capacity (for workers it's their buzzing)
        for sub in subs:
            sub_children = SwarmMember.query.filter_by(parent_member_id=sub.id).all()
            if sub_children:
                sub.capacity = sum((c.buzzing or 0) for c in sub_children)
            else:
                sub.capacity = sub.buzzing or 0

        # Calculate fractions among subordinates
        total_sub_capacity = sum((s.capacity or 0) for s in subs)
        for sub in subs:
            if total_sub_capacity > 0:
                sub.fraction = (sub.capacity or 0) / total_sub_capacity
            else:
                sub.fraction = 1.0 / len(subs) if subs else 0

        # This member's capacity = sum of subordinate buzzings
        member.capacity = sum((s.buzzing or 0) for s in subs)
    else:
        member.capacity = member.buzzing or 0

    # Second: recalculate fractions among this member's SIBLINGS
    total_capacity = member.capacity or 0
    if member.parent_member_id is not None:
        siblings = SwarmMember.query.filter_by(
            parent_member_id=member.parent_member_id,
            swarm_id=member.swarm_id
        ).all()
        total_capacity = sum((s.capacity or 0) for s in siblings)
        for sibling in siblings:
            if total_capacity > 0:
                sibling.fraction = (sibling.capacity or 0) / total_capacity
            else:
                sibling.fraction = 1.0 / len(siblings) if siblings else 0
    else:
        # Top-level member (no parent) — fraction is 1.0
        member.fraction = 1.0

    db.session.commit()

    return jsonify({
        'ok': True,
        'member_id': member.id,
        'capacity': member.capacity,
        'fraction': member.fraction,
        'total_sibling_capacity': total_capacity,
    })


@app.route('/api/member/<int:member_id>/fractions', methods=['GET'])
@csrf.exempt
def api_member_fractions(member_id):
    """Return this member's subordinates with their fractions — used by boss to split work."""
    member = SwarmMember.query.get_or_404(member_id)
    subs = SwarmMember.query.filter_by(parent_member_id=member.id).all()

    total_capacity = sum((s.capacity or 0) for s in subs)

    return jsonify({
        'member_id': member.id,
        'total_capacity': total_capacity,
        'subordinates': [{
            'member_id': s.id,
            'username': s.user.username,
            'member_type': s.member_type,
            'fraction': s.fraction,
            'buzzing': s.buzzing,
            'capacity': s.capacity,
        } for s in subs]
    })


# ── Multimedia file serving ──────────────────────────────────────────────────

@app.route('/uploads/<path:filepath>')
def serve_upload(filepath):
    """Serve uploaded multimedia files to GiantHoneyBee clients fetching over HTTP.
    TODO (hardening): add auth for non-localhost callers before production.
    Security: safe_join blocks directory traversal; 404 on missing files.
    No autoindex — only explicit paths are served.
    """
    # Block any traversal attempts that survive routing
    if '..' in filepath or filepath.startswith('/'):
        abort(404)
    try:
        safe_path = safe_join(UPLOADS_ROOT, filepath)
    except Exception:
        abort(404)

    if not os.path.isfile(safe_path):
        abort(404)

    directory = os.path.dirname(safe_path)
    filename = os.path.basename(safe_path)
    return send_from_directory(directory, filename, as_attachment=False)


# ── Multimedia piece upload API ───────────────────────────────────────────────

@app.route('/api/component/<int:component_id>/upload-piece', methods=['POST'])
@csrf.exempt
def api_upload_piece(component_id):
    """GiantHoneyBee tier clients upload a cut piece (tile / audio slice / video clip).

    Multipart form fields:
      piece_path       (str)  — server-relative path under uploads/, e.g.
                                 'photo/swarmjob_42/cut_by_raja/grid_a_q1.jpg'
      piece            (file) — binary content of the piece
      audio_piece_path (str)  — optional; for video pieces only
      audio_piece      (file) — optional; for video pieces only

    Auth: Bearer token (same pattern as other tier-client endpoints).
    Returns: {ok: true, piece_path: ..., audio_piece_path: ...}
    """
    # Auth: require a valid Bearer token (same helper used by other API endpoints)
    api_user = get_api_user()
    if api_user is None:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    comp = JobComponent.query.get_or_404(component_id)

    piece_path_rel = request.form.get('piece_path')
    if not piece_path_rel:
        return jsonify({'ok': False, 'error': 'piece_path field required'}), 400
    if 'piece' not in request.files:
        return jsonify({'ok': False, 'error': 'piece file required'}), 400

    # Validate and write primary piece
    if '..' in piece_path_rel or piece_path_rel.startswith('/'):
        return jsonify({'ok': False, 'error': 'Invalid piece_path'}), 400
    try:
        abs_piece_path = safe_join(UPLOADS_ROOT, piece_path_rel)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid piece_path'}), 400

    os.makedirs(os.path.dirname(abs_piece_path), exist_ok=True)
    request.files['piece'].save(abs_piece_path)
    comp.piece_path = piece_path_rel

    # Optional audio piece (video components)
    audio_piece_path_rel = request.form.get('audio_piece_path')
    if audio_piece_path_rel and 'audio_piece' in request.files:
        if '..' in audio_piece_path_rel or audio_piece_path_rel.startswith('/'):
            return jsonify({'ok': False, 'error': 'Invalid audio_piece_path'}), 400
        try:
            abs_audio_path = safe_join(UPLOADS_ROOT, audio_piece_path_rel)
        except Exception:
            return jsonify({'ok': False, 'error': 'Invalid audio_piece_path'}), 400

        os.makedirs(os.path.dirname(abs_audio_path), exist_ok=True)
        request.files['audio_piece'].save(abs_audio_path)
        comp.audio_piece_path = audio_piece_path_rel

    db.session.commit()

    return jsonify({
        'ok': True,
        'component_id': comp.id,
        'piece_path': comp.piece_path,
        'audio_piece_path': comp.audio_piece_path,
    })


# ── Init DB ───────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8877, debug=True)

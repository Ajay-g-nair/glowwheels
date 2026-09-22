from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import db
from models import User
from config import Config

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin authorization required.', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def worker_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['worker', 'admin']:
            flash('Worker authorization required.', 'danger')
            return redirect(url_for('auth.worker_login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    next_page = request.args.get('next')

    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '').strip()

        if not login_input or not password:
            flash('Please provide both username/phone and password.', 'danger')
            return render_template('auth/login.html', next=next_page, config=Config)

        user = User.query.filter(
            (User.username == login_input) | 
            (User.phone == login_input) | 
            (User.email == login_input)
        ).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name or user.username

            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'worker':
                return redirect(url_for('worker.dashboard'))
            else:
                return redirect(next_page or url_for('user.index'))
        else:
            flash('Invalid credentials. Please verify your phone/username and password.', 'danger')

    return render_template('auth/login.html', next=next_page, config=Config)

@auth_bp.route('/worker/login', methods=['GET', 'POST'])
def worker_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        worker = User.query.filter_by(username=username).first()
        if worker and worker.role in ['worker', 'admin'] and worker.check_password(password):
            session['user_id'] = worker.id
            session['username'] = worker.username
            session['role'] = worker.role
            session['full_name'] = worker.full_name or worker.username

            flash(f'Welcome, {worker.full_name or worker.username}! Worker operations dashboard active.', 'success')
            return redirect(url_for('worker.dashboard'))
        else:
            flash('Invalid worker credentials. Please check your staff ID and password.', 'danger')

    return render_template('auth/worker_login.html', config=Config)

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Check against Config admin credentials
        if username.lower() == Config.ADMIN_USERNAME.lower() and password == Config.ADMIN_PASSWORD:
            admin_user = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
            if not admin_user:
                admin_user = User(
                    username=Config.ADMIN_USERNAME,
                    full_name='GlowWheels Admin',
                    role='admin'
                )
                admin_user.set_password(Config.ADMIN_PASSWORD)
                db.session.add(admin_user)
                db.session.commit()

            session['user_id'] = admin_user.id
            session['username'] = admin_user.username
            session['role'] = 'admin'
            session['full_name'] = admin_user.full_name or 'Admin'
            flash('Administrator authenticated. Welcome to GlowWheels Command Center.', 'success')
            return redirect(url_for('admin.dashboard'))

        # Check in DB for any other admin account
        admin_db = User.query.filter_by(username=username, role='admin').first()
        if admin_db and admin_db.check_password(password):
            session['user_id'] = admin_db.id
            session['username'] = admin_db.username
            session['role'] = 'admin'
            session['full_name'] = admin_db.full_name or 'Admin'
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin.dashboard'))

        flash('Invalid administrator credentials.', 'danger')

    return render_template('auth/admin_login.html', config=Config)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        username = request.form.get('username', '').strip() or phone
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not phone or not password:
            flash('Phone number and password are required.', 'danger')
            return render_template('auth/register_user.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_user.html')

        if User.query.filter((User.username == username) | (User.phone == phone)).first():
            flash('An account with this phone number or username already exists.', 'danger')
            return render_template('auth/register_user.html')

        user = User(
            username=username,
            full_name=full_name or 'Valued Customer',
            phone=phone,
            email=email or None,
            role='user'
        )
        user.set_password(password)
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Registration could not be completed: {e}', 'danger')
            return render_template('auth/register_user.html')

        flash('Account created successfully! Please sign in to book your wash.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_user.html')

@auth_bp.route('/worker/register', methods=['GET', 'POST'])
def register_worker():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not username or not password or not phone:
            flash('Full name, username, phone and password are required.', 'danger')
            return render_template('auth/register_worker.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_worker.html')

        if User.query.filter_by(username=username).first():
            flash('Worker username already taken.', 'danger')
            return render_template('auth/register_worker.html')

        worker = User(
            username=username,
            full_name=full_name or username,
            phone=phone,
            email=email or None,
            role='worker'
        )
        worker.set_password(password)
        try:
            db.session.add(worker)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Worker registration could not be completed: {e}', 'danger')
            return render_template('auth/register_worker.html')

        flash('Staff account registered! Please sign in to the Worker Portal.', 'success')
        return redirect(url_for('auth.worker_login'))

    return render_template('auth/register_worker.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('user.index'))

import random
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)


def generate_unique_account_number():
    """Generate a unique 12-digit account number."""
    while True:
        acc_num = str(random.randint(100000000000, 999999999999))
        if not User.query.filter_by(account_number=acc_num).first():
            return acc_num


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip().lower()
        phone_number = request.form.get('phone_number', '').strip()
        password = request.form.get('password', '')
        confirm_pw = request.form.get('confirm_password', '')

        # Validations
        if not all([full_name, email, username, password, confirm_pw]):
            flash('All required fields must be filled.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_pw:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must contain at least 6 characters.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('This username is already taken. Please choose another.', 'danger')
            return render_template('auth/register.html')

        new_account_number = generate_unique_account_number()
        new_user = User(
            full_name=full_name,
            email=email,
            username=username,
            phone_number=phone_number or None,
            account_number=new_account_number,
            balance=0.0,
            role='customer',
            is_active=True
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash(
            f'Account successfully created! Your account number is {new_account_number}. Please sign in.',
            'success'
        )
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        if not identifier or not password:
            flash('Please enter both your username/email and password.', 'warning')
            return render_template('auth/login.html')

        # Allow logging in with either username or email
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated or frozen. Please contact customer support.', 'danger')
                return render_template('auth/login.html')

            login_user(user, remember=remember)
            flash(f'Welcome back, {user.full_name}!', 'success')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)

            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip().lower()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not identifier or not new_password or not confirm_password:
            flash('All fields are required to reset your password.', 'danger')
            return render_template('auth/forgot_password.html')

        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('auth/forgot_password.html')

        if len(new_password) < 6:
            flash('New password must be at least 6 characters.', 'danger')
            return render_template('auth/forgot_password.html')

        user = User.query.filter(
            (User.email == identifier) | (User.username == identifier) | (User.account_number == identifier)
        ).first()

        if not user:
            # Mask user existence for security or provide helpful feedback
            flash('If an account matches those details, your password has been reset.', 'info')
            return redirect(url_for('auth.login'))

        user.set_password(new_password)
        db.session.commit()
        flash('Password successfully reset! You can now log in with your new credentials.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been safely logged out. Thank you for banking with us.', 'info')
    return redirect(url_for('auth.login'))

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models.user import User
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()
audit_service = AuditService()


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            payload = {
                'full_name': request.form.get('full_name', ''),
                'email': request.form.get('email', ''),
                'password': request.form.get('password', ''),
                'role': request.form.get('role', 'candidate'),
                'phone': request.form.get('phone', ''),
                'location': request.form.get('location', ''),
                'skills': [item.strip() for item in request.form.get('skills', '').split(',') if item.strip()],
            }
            user = auth_service.register(payload)
            logged_in_user = User.from_dict(user)
            session.clear()
            login_user(logged_in_user)
            session.permanent = True
            session['role'] = user.get('role')
            audit_service.record(user['id'], 'user.registered', 'user', user['id'])
            flash('Registration successful.', 'success')
            response = redirect(url_for('dashboard.index'))
            response.set_cookie(
                'hirehub_role',
                user.get('role'),
                httponly=True,
                secure=current_app.config['SESSION_COOKIE_SECURE'],
                samesite='Lax',
            )
            return response
        except ValueError as exc:
            flash(str(exc), 'danger')
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = auth_service.login(email, password)
        if user:
            logged_in_user = User.from_dict(user)
            session.clear()
            login_user(logged_in_user)
            session.permanent = True
            session['role'] = user.get('role')
            audit_service.record(user['id'], 'user.logged_in', 'user', user['id'])
            response = redirect(url_for('dashboard.index'))
            response.set_cookie(
                'hirehub_role',
                user.get('role'),
                httponly=True,
                secure=current_app.config['SESSION_COOKIE_SECURE'],
                samesite='Lax',
            )
            return response
        flash('Invalid credentials.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    audit_service.record(current_user.get_id(), 'user.logged_out', 'user', current_user.get_id())
    logout_user()
    session.clear()
    response = redirect(url_for('auth.login'))
    response.delete_cookie('hirehub_role')
    return response

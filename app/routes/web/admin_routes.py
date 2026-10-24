import csv
from io import BytesIO, StringIO

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from app.repositories.user_repository import UserRepository
from app.repositories.job_repository import JobRepository
from app.repositories.application_repository import ApplicationRepository
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.utils.decorators import role_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    users = UserRepository().get_all()
    jobs = JobRepository().get_all()
    applications = ApplicationRepository().get_all()
    metrics = AnalyticsService().get_dashboard_metrics()
    return render_template('admin/dashboard.html', users=users, jobs=jobs, applications=applications, metrics=metrics)


@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    users = UserRepository().get_all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/reports')
@login_required
@role_required('admin')
def reports():
    users = UserRepository().get_all()
    jobs = JobRepository().get_all()
    applications = ApplicationRepository().get_all()
    metrics = AnalyticsService().get_dashboard_metrics()
    return render_template('admin/reports.html', users=users, jobs=jobs, applications=applications, metrics=metrics)


@admin_bp.route('/reports/export.csv')
@login_required
@role_required('admin')
def export_reports():
    users = UserRepository().get_all()
    jobs = JobRepository().get_all()
    applications = ApplicationRepository().get_all()
    metrics = AnalyticsService().get_dashboard_metrics()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['section', 'metric', 'value'])
    for key, value in metrics.items():
        if isinstance(value, dict):
            for status, count in value.items():
                writer.writerow([key, status, count])
        else:
            writer.writerow(['overview', key, value])
    writer.writerow(['detail', 'users', len(users)])
    writer.writerow(['detail', 'jobs', len(jobs)])
    writer.writerow(['detail', 'applications', len(applications)])
    AuditService().record(current_user.id, 'admin.report_exported', 'report', 'overview')
    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='hirehub-report.csv',
    )


@admin_bp.route('/audit-logs')
@login_required
@role_required('admin')
def audit_logs():
    logs = AuditService().get_recent()
    users = {user['id']: user for user in UserRepository().get_all()}
    return render_template('admin/audit_logs.html', logs=logs, users=users)


@admin_bp.route('/users/<user_id>/role', methods=['POST'])
@login_required
@role_required('admin')
def update_user_role(user_id):
    role = request.form.get('role', '')
    if role not in {'candidate', 'recruiter', 'admin'}:
        flash('Select a valid user role.', 'danger')
    elif user_id == current_user.id and role != 'admin':
        flash('You cannot remove your own admin role.', 'danger')
    elif UserRepository().update(user_id, {'role': role}):
        AuditService().record(current_user.id, 'admin.user_role_updated', 'user', user_id, role)
        flash('User role updated.', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('admin.users'))


@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def profile():
    user_repository = UserRepository()
    if request.method == 'POST':
        updates = {
            'full_name': request.form.get('full_name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'location': request.form.get('location', '').strip(),
        }
        if not updates['full_name']:
            flash('Name is required.', 'danger')
        else:
            user_repository.update_profile(current_user.id, updates)
            for field, value in updates.items():
                setattr(current_user, field, value)
            AuditService().record(current_user.id, 'admin.profile_updated', 'user', current_user.id)
            flash('Profile updated.', 'success')
    return render_template('admin/profile.html', user=current_user)

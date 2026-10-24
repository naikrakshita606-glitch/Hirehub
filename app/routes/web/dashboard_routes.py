from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.services.analytics_service import AnalyticsService
from app.utils.decorators import role_required


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.role == 'candidate':
        return redirect(url_for('candidate.dashboard'))
    if current_user.role == 'recruiter':
        return redirect(url_for('recruiter.dashboard'))
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))


@dashboard_bp.route('/dashboard/overview')
@login_required
@role_required('admin')
def overview():
    metrics = AnalyticsService().get_dashboard_metrics()
    return render_template('dashboard/overview.html', metrics=metrics)

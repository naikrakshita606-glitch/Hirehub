from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.services.audit_service import AuditService
from app.services.analytics_service import AnalyticsService
from app.utils.decorators import api_role_required

analytics_api_bp = Blueprint('analytics_api', __name__)


@analytics_api_bp.route('/analytics/overview', methods=['GET'])
@login_required
@api_role_required('admin')
def overview_api():
    metrics = AnalyticsService().get_dashboard_metrics()
    return jsonify(metrics)


@analytics_api_bp.route('/reports', methods=['GET'])
@login_required
@api_role_required('admin')
def reports_api():
    return jsonify(AnalyticsService().get_dashboard_metrics())


@analytics_api_bp.route('/audit-logs', methods=['GET'])
@login_required
@api_role_required('admin')
def audit_logs_api():
    limit = min(max(request.args.get('limit', 100, type=int), 1), 500)
    logs = AuditService().get_recent(limit=limit)
    return jsonify({
        'audit_logs': [
            {key: value for key, value in entry.items() if key != '_id'}
            for entry in logs
        ]
    })

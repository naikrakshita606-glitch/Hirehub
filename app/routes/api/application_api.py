from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.application_service import ApplicationService
from app.repositories.application_repository import ApplicationRepository
from app.utils.decorators import api_role_required

application_api_bp = Blueprint('application_api', __name__)
application_service = ApplicationService()


@application_api_bp.route('/applications', methods=['POST'])
@login_required
@api_role_required('candidate')
def create_application_api():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({'error': 'JSON object required'}), 400
    payload['candidate_id'] = current_user.id
    try:
        application = application_service.apply(payload)
        return jsonify({'message': 'application submitted', 'application': public_record(application)}), 201
    except (ValueError, KeyError) as exc:
        return jsonify({'error': str(exc)}), 400


@application_api_bp.route('/applications', methods=['GET'])
@login_required
def list_applications_api():
    repository = ApplicationRepository()
    if current_user.role == 'candidate':
        applications = repository.get_for_candidate(current_user.id)
    elif current_user.role == 'recruiter':
        applications = repository.get_for_recruiter(current_user.id)
    elif current_user.role == 'admin':
        applications = repository.get_all()
    else:
        return jsonify({'error': 'forbidden'}), 403
    return jsonify({'applications': [public_record(item) for item in applications]})


@application_api_bp.route('/applications/<application_id>/status', methods=['PATCH'])
@login_required
@api_role_required('recruiter')
def update_application_status_api(application_id):
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({'error': 'JSON object required'}), 400
    try:
        application = application_service.update_status(application_id, current_user.id, payload.get('status', ''))
        return jsonify({'application': public_record(application)})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


def public_record(record):
    return {key: value for key, value in record.items() if key != '_id'}

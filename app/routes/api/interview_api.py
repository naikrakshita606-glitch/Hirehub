from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.interview_service import InterviewService
from app.repositories.interview_repository import InterviewRepository
from app.utils.decorators import api_role_required

interview_api_bp = Blueprint('interview_api', __name__)
interview_service = InterviewService()


@interview_api_bp.route('/interviews', methods=['POST'])
@login_required
@api_role_required('recruiter')
def schedule_interview_api():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({'error': 'JSON object required'}), 400
    payload['recruiter_id'] = current_user.id
    try:
        interview = interview_service.schedule(payload)
        return jsonify({'message': 'interview scheduled', 'interview': public_record(interview)}), 201
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@interview_api_bp.route('/interviews', methods=['GET'])
@login_required
def list_interviews_api():
    interviews = InterviewRepository().get_all()
    if current_user.role != 'admin':
        key = 'candidate_id' if current_user.role == 'candidate' else 'recruiter_id'
        interviews = [item for item in interviews if item.get(key) == current_user.id]
    return jsonify({'interviews': [public_record(item) for item in interviews]})


@interview_api_bp.route('/interviews/<interview_id>', methods=['PATCH'])
@login_required
@api_role_required('recruiter')
def update_interview_api(interview_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({'error': 'JSON object required'}), 400
    try:
        interview = interview_service.update(interview_id, current_user.id, payload)
        return jsonify({'interview': public_record(interview)})
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


def public_record(record):
    return {key: value for key, value in record.items() if key != '_id'}
